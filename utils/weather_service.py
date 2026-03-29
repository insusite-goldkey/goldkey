# ══════════════════════════════════════════════════════════════════════════════
# [GP-WEATHER] 사용자 위치 기반 실시간 날씨 서비스
# 
# 목적: 브라우저 Geolocation API로 사용자 기기의 GPS 좌표를 획득하여
#       해당 위치의 실시간 날씨 정보를 제공
# 
# 구성:
#   1. 클라이언트 GPS 좌표 획득 (streamlit-js-eval)
#   2. 좌표 → 한국 주소 변환 (네이버 Geocoding API)
#   3. 실시간 날씨 조회 (OpenWeatherMap API)
#   4. 출력 형식: "🌤️ 오늘의 날씨: 맑음 +16°C 습도55%"
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
from typing import Optional, Tuple


def get_user_location_gps() -> Tuple[Optional[float], Optional[float]]:
    """
    [GP-WEATHER §1] 브라우저 Geolocation API로 사용자 GPS 좌표 획득.
    
    Returns:
        (latitude, longitude) 또는 (None, None) if failed
    
    Note:
        - 사용자가 위치 권한을 거부하면 None 반환
        - HTTPS 환경에서만 작동 (로컬 개발 시 localhost 허용)
    """
    try:
        from streamlit_js_eval import get_geolocation
        
        # 세션에 캐시된 위치 정보 확인 (당일 1회만 조회)
        import datetime
        _today_key = f"_gps_location_{datetime.date.today().strftime('%Y%m%d')}"
        
        if _today_key in st.session_state:
            cached = st.session_state[_today_key]
            if cached and isinstance(cached, dict):
                return cached.get("lat"), cached.get("lon")
        
        # Geolocation API 호출
        location = get_geolocation()
        
        if location and isinstance(location, dict):
            lat = location.get("coords", {}).get("latitude")
            lon = location.get("coords", {}).get("longitude")
            
            if lat is not None and lon is not None:
                # 세션 캐시 저장
                st.session_state[_today_key] = {"lat": lat, "lon": lon}
                return float(lat), float(lon)
    
    except Exception:
        pass
    
    return None, None


def convert_coords_to_korean_address(lat: float, lon: float) -> str:
    """
    [GP-WEATHER §2] 좌표를 한국 주소로 변환 (네이버 Geocoding API).
    
    Args:
        lat: 위도
        lon: 경도
    
    Returns:
        한국 주소 (예: "강남구 역삼동") 또는 빈 문자열
    
    Note:
        - 네이버 클라우드 플랫폼 Geocoding API 사용
        - API 키는 st.secrets["NAVER_CLIENT_ID"], st.secrets["NAVER_CLIENT_SECRET"]
    """
    try:
        import requests
        from shared_components import get_env_secret
        
        client_id = get_env_secret("NAVER_CLIENT_ID", "")
        client_secret = get_env_secret("NAVER_CLIENT_SECRET", "")
        
        if not client_id or not client_secret:
            return ""
        
        # 네이버 Reverse Geocoding API
        url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
        params = {
            "coords": f"{lon},{lat}",
            "orders": "roadaddr,addr",
            "output": "json"
        }
        headers = {
            "X-NCP-APIGW-API-KEY-ID": client_id,
            "X-NCP-APIGW-API-KEY": client_secret
        }
        
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            
            if results:
                # 도로명 주소 우선
                region = results[0].get("region", {})
                area1 = region.get("area1", {}).get("name", "")  # 시/도
                area2 = region.get("area2", {}).get("name", "")  # 구
                area3 = region.get("area3", {}).get("name", "")  # 동
                
                # "서울특별시" → "서울", "경기도" → "경기" 간소화
                if area1.endswith("특별시") or area1.endswith("광역시"):
                    area1 = area1[:-3]
                elif area1.endswith("도"):
                    area1 = area1[:-1]
                
                # 구 + 동 조합 (예: "강남구 역삼동")
                if area2 and area3:
                    return f"{area2} {area3}"
                elif area2:
                    return area2
                elif area1:
                    return area1
    
    except Exception:
        pass
    
    return ""


def fetch_weather_by_coords(lat: float, lon: float) -> dict:
    """
    [GP-WEATHER §3] 좌표 기반 실시간 날씨 조회 (OpenWeatherMap API).
    
    Args:
        lat: 위도
        lon: 경도
    
    Returns:
        {
            "status": str,  # 날씨 상태 (맑음/흐림/비/눈 등)
            "temp": float,  # 기온 (섭씨)
            "humidity": int,  # 습도 (%)
            "icon": str  # 이모지 아이콘
        }
    
    Note:
        - OpenWeatherMap API 키: st.secrets["OPENWEATHER_API_KEY"]
        - 무료 플랜: 1분당 60회 호출 제한
    """
    try:
        import requests
        from shared_components import get_env_secret
        
        api_key = get_env_secret("OPENWEATHER_API_KEY", "")
        
        if not api_key:
            return {}
        
        # OpenWeatherMap Current Weather API
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",  # 섭씨 온도
            "lang": "kr"  # 한국어
        }
        
        resp = requests.get(url, params=params, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            
            # 날씨 상태
            weather_main = data.get("weather", [{}])[0].get("main", "")
            weather_desc = data.get("weather", [{}])[0].get("description", "")
            
            # 기온 및 습도
            temp = data.get("main", {}).get("temp", 0)
            humidity = data.get("main", {}).get("humidity", 0)
            
            # 날씨 상태 한글 매핑
            status_map = {
                "Clear": "맑음",
                "Clouds": "흐림",
                "Rain": "비",
                "Drizzle": "이슬비",
                "Snow": "눈",
                "Thunderstorm": "천둥번개",
                "Mist": "안개",
                "Fog": "안개",
                "Haze": "실안개"
            }
            status = status_map.get(weather_main, weather_desc)
            
            # 이모지 아이콘
            icon_map = {
                "Clear": "☀️",
                "Clouds": "☁️",
                "Rain": "🌧️",
                "Drizzle": "🌦️",
                "Snow": "❄️",
                "Thunderstorm": "⛈️",
                "Mist": "🌫️",
                "Fog": "🌫️",
                "Haze": "🌫️"
            }
            icon = icon_map.get(weather_main, "🌤️")
            
            return {
                "status": status,
                "temp": round(temp, 1),
                "humidity": int(humidity),
                "icon": icon
            }
    
    except Exception:
        pass
    
    return {}


def get_weather_briefing_text(
    use_gps: bool = True,
    fallback_to_ip: bool = True,
    user_id: str = ""
) -> str:
    """
    [GP-WEATHER §4] 날씨 브리핑 텍스트 생성 (최종 출력) — 3단계 폴백.
    
    Args:
        use_gps: True이면 GPS 좌표 우선 사용
        fallback_to_ip: GPS 실패 시 IP 기반 위치로 폴백
        user_id: 회원 프로필 기반 폴백용 사용자 ID (3단계)
    
    Returns:
        "🌤️ 오늘의 날씨: 맑음 +16°C 습도55%" 형식의 문자열
        실패 시 빈 문자열 반환
    
    Note:
        - [Seoul, South Korea] 같은 영문 표기 절대 포함 안 함
        - 위치 정보는 한국어 주소로만 표시
        - 3단계 폴백: GPS → IP → 회원 프로필
    """
    lat, lon = None, None
    location_label = ""
    
    # [1단계] GPS 좌표 획득 시도
    if use_gps:
        lat, lon = get_user_location_gps()
        
        if lat is not None and lon is not None:
            # 좌표 → 한국 주소 변환
            location_label = convert_coords_to_korean_address(lat, lon)
    
    # [2단계] GPS 실패 시 IP 기반 폴백
    if (lat is None or lon is None) and fallback_to_ip:
        try:
            # voice_engine.py의 IP 기반 함수 재사용
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from voice_engine import _approx_latlon_from_ip
            
            lat, lon, ip_city = _approx_latlon_from_ip()
            
            # IP 기반 도시명에서 영문 제거 (한국어만 추출)
            if ip_city:
                # "Seoul, South Korea" → "Seoul" 추출 후 한글 매핑
                city_name = ip_city.split(",")[0].strip()
                
                # 주요 도시 한글 매핑
                city_kr_map = {
                    "Seoul": "서울",
                    "Busan": "부산",
                    "Incheon": "인천",
                    "Daegu": "대구",
                    "Daejeon": "대전",
                    "Gwangju": "광주",
                    "Ulsan": "울산",
                    "Suwon": "수원",
                    "Goyang": "고양",
                    "Seongnam": "성남"
                }
                
                location_label = city_kr_map.get(city_name, "")
        
        except Exception:
            pass
    
    # [3단계] IP 실패 시 회원 프로필 기반 폴백
    if (lat is None or lon is None) and user_id:
        try:
            from db_utils import _get_sb
            sb = _get_sb()
            if sb:
                # gk_members 테이블에서 회원 정보 조회
                member_resp = sb.table("gk_members").select("company, region").eq("user_id", user_id).limit(1).execute()
                
                if member_resp.data and len(member_resp.data) > 0:
                    member = member_resp.data[0]
                    region = member.get("region", "")
                    company = member.get("company", "")
                    
                    # region 또는 company에서 도시명 추출
                    location_text = region or company or ""
                    
                    # 주요 도시명 매핑 (회원 프로필에서 추출)
                    city_coords = {
                        "서울": (37.5665, 126.9780),
                        "부산": (35.1796, 129.0756),
                        "인천": (37.4563, 126.7052),
                        "대구": (35.8714, 128.6014),
                        "대전": (36.3504, 127.3845),
                        "광주": (35.1595, 126.8526),
                        "울산": (35.5384, 129.3114),
                        "수원": (37.2636, 127.0286),
                        "고양": (37.6584, 126.8320),
                        "성남": (37.4449, 127.1388)
                    }
                    
                    # 텍스트에서 도시명 찾기
                    for city, coords in city_coords.items():
                        if city in location_text:
                            lat, lon = coords
                            location_label = city
                            break
        
        except Exception:
            pass
    
    # [4단계] 날씨 정보 조회
    if lat is not None and lon is not None:
        weather_data = fetch_weather_by_coords(lat, lon)
        
        if weather_data:
            status = weather_data.get("status", "")
            temp = weather_data.get("temp", 0)
            humidity = weather_data.get("humidity", 0)
            icon = weather_data.get("icon", "🌤️")
            
            # 온도 부호 처리
            temp_str = f"+{temp}" if temp >= 0 else str(temp)
            
            # 최종 출력 형식: "🌤️ 오늘의 날씨: 맑음 +16°C 습도55%"
            # 위치 라벨은 포함하지 않음 (사용자 지시사항)
            return f"{icon} 오늘의 날씨: {status} {temp_str}°C 습도{humidity}%"
    
    return ""


def get_location_label_only(use_gps: bool = True) -> str:
    """
    [GP-WEATHER §5] 위치 라벨만 반환 (날씨 정보 없이).
    
    Returns:
        "강남구 역삼동" 또는 "서울" 형식의 한국어 주소
        실패 시 "현재 위치" 반환
    """
    lat, lon = None, None
    
    if use_gps:
        lat, lon = get_user_location_gps()
        
        if lat is not None and lon is not None:
            location = convert_coords_to_korean_address(lat, lon)
            if location:
                return location
    
    # IP 기반 폴백
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from voice_engine import _approx_latlon_from_ip
        
        _, _, ip_city = _approx_latlon_from_ip()
        
        if ip_city:
            city_name = ip_city.split(",")[0].strip()
            city_kr_map = {
                "Seoul": "서울",
                "Busan": "부산",
                "Incheon": "인천",
                "Daegu": "대구",
                "Daejeon": "대전",
                "Gwangju": "광주",
                "Ulsan": "울산"
            }
            kr_name = city_kr_map.get(city_name, "")
            if kr_name:
                return kr_name
    
    except Exception:
        pass
    
    return "현재 위치"
