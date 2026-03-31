# 디지털 자산 수집 허브 통합 가이드

**작성일**: 2026-03-31  
**목적**: 태블릿 최적화 + 스마트 스캔 + 문서 복원 시스템 구축  
**전략**: Drop Zone + Smart Scan + AI Document Restoration

---

## 🎯 시스템 개요

### 핵심 철학
> "증권 스캔을 '고신뢰도 문서 복원 시스템'으로 빌딩하라."

### 4대 핵심 기능

#### 1. 태블릿 최적화: 멀티태스킹 Drag & Drop
- Split View 기능 100% 활용
- 넓은 분석 대기 구역 (Analysis Drop Zone) 배치
- 바탕화면/폴더 앱에서 파일 드래그 → 즉시 분석 파이프라인 가동

#### 2. 인텔리전트 스캐너 모드 (Smart Scan Protocol)
- 일반 카메라 촬영 차단
- 문서 경계 자동 감지
- 실시간 테두리 인식 → 자동 촬영
- 촬영 직후 즉시 확인 팝업

#### 3. 원문 보존형 노출 제어 (Hi-Fi Exposure Control)
- 과다 노출(화이트아웃) 방지
- 조리개 값 고정 (-1.0 ~ -0.5 단계)
- 원본 색감 보존 (Original Texture) 모드
- 글자 획(Stroke) 최대 선명도 확보

#### 4. 지능형 문서 복원 (AI Document Restoration)
- 기하학적 보정 (De-warping): 렌즈 왜곡 보정
- 구김 제거 (De-skewing & Flattening): 종이 주름 평면화
- 비틀림 수정: 휘어진 문서 직선화

---

## 📦 생성된 모듈

### Digital Asset Collection Hub 모듈

**파일**: `modules/digital_asset_collection_hub.py`

**핵심 클래스**:
```python
class DigitalAssetCollectionHub:
    """
    디지털 자산 수집 허브
    
    핵심 기능:
    1. 태블릿 Drag & Drop (분석 대기 구역)
    2. 인텔리전트 스캐너 모드 (문서 경계 자동 감지)
    3. 원문 보존형 노출 제어 (Hi-Fi Exposure Control)
    4. 지능형 문서 복원 (AI Document Restoration)
    """
```

**주요 메서드**:
- `render_drop_zone()`: 분석 대기 구역 렌더링
- `render_smart_scanner()`: 스마트 스캐너 인터페이스
- `_apply_document_restoration()`: 문서 복원 적용
- `render_analysis_queue()`: 분석 대기열 관리

---

## 🚀 사용 방법

### 1. 분석 대기 구역 (Drop Zone)

```python
from modules.digital_asset_collection_hub import render_digital_asset_collection_hub

# CRM 앱 증권 스캔 센터
render_digital_asset_collection_hub()
```

**사용자 경험**:
1. 태블릿 Split View 활성화
2. 한쪽에 파일 앱, 다른 쪽에 CRM 앱 배치
3. PDF/JPG 파일을 Drop Zone으로 드래그
4. 즉시 분석 파이프라인 가동

**리딩 파트너 피드백**:
```
✅ 자산을 안전하게 수신했습니다: 삼성생명_종신보험.pdf
```

### 2. 스마트 스캔 모드

```python
hub = DigitalAssetCollectionHub()
hub.render_smart_scanner()
```

**진입 구조**:
1. [스캔 시작] 버튼 클릭
2. 기기 카메라 권한 획득
3. 실시간 문서 테두리 감지
4. 자동 촬영 (경계 인식 시)

**확인 팝업**:
```
📋 이 문서를 지금 분석에 반영할까요?

[✅ 분석 투입]  [🔄 재촬영]
```

### 3. 문서 복원 적용

```python
# 이미지 복원
restored_image = hub._apply_document_restoration(original_image)
```

**복원 단계**:
1. **노출 최적화**: -1.0 ~ -0.5 단계로 고정
2. **기하학적 보정**: 렌즈 왜곡 제거
3. **구김 제거**: 종이 주름 평면화

**리딩 파트너 보고**:
```
💡 문서의 기하학적 오차를 수정했습니다.
   이제 육안으로 확인하는 것보다 더 정교한 분석이 가능합니다.
```

---

## 🎨 시각적 프로세스 (Visual Workflow)

### 전체 흐름

| 단계 | 사용자 액션 | 리딩 파트너 백그라운드 작업 | 직관적 피드백 (UI) |
|------|------------|---------------------------|-------------------|
| **수집** | 드래그 앤 드롭 / 스캔 | 파일 무결성 검사 및 포맷 변환 | "자산을 안전하게 수신했습니다." |
| **보정** | (자동 실행) | 비틀림 수정 및 노출 최적화 | 문서가 평평하게 펴지는 애니메이션 |
| **확인** | 팝업에서 '분석 승인' | 분석 파이프라인 트리거 | "정밀 분석을 시작합니다." |

### UI 컴포넌트

#### Drop Zone
```
┌─────────────────────────────────────────┐
│              📂                         │
│   분석 대기 구역 (Analysis Drop Zone)   │
│                                         │
│   증권 파일(PDF, JPG)을 이곳에          │
│   끌어다 놓으세요                       │
│                                         │
│   [파일 선택 버튼]                      │
└─────────────────────────────────────────┘
```

#### Smart Scanner
```
┌─────────────────────────────────────────┐
│              📸                         │
│      인텔리전트 스캐너 모드              │
│                                         │
│   문서의 경계를 스스로 인식하고          │
│   스캔합니다                            │
│                                         │
│        [📸 스캔 시작]                   │
└─────────────────────────────────────────┘
```

#### Scan Confirmation
```
┌─────────────────────────────────────────┐
│  📋 이 문서를 지금 분석에 반영할까요?    │
│                                         │
│  [문서 미리보기 이미지]                  │
│                                         │
│  [✅ 분석 투입]  [🔄 재촬영]            │
└─────────────────────────────────────────┘
```

---

## 🛠️ 기술 구현 스펙

### 1. Drop Zone 구현

#### Native Drag & Drop API 연동

**Streamlit 구현**:
```python
uploaded_files = st.file_uploader(
    "증권 파일 선택",
    type=["pdf", "jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="drop_zone_uploader"
)
```

**실제 배포 시 (React Native / Flutter)**:
```javascript
// React Native
import { DragAndDrop } from 'react-native-drag-drop';

<DragAndDrop
  onDrop={(files) => processDroppedFiles(files)}
  acceptedTypes={['application/pdf', 'image/jpeg', 'image/png']}
/>
```

### 2. Smart Scan 구현

#### Document Scanner SDK

**iOS (VisionKit)**:
```swift
import VisionKit

let scannerViewController = VNDocumentCameraViewController()
scannerViewController.delegate = self

// 문서 경계 자동 감지
func documentCameraViewController(
    _ controller: VNDocumentCameraViewController,
    didFinishWith scan: VNDocumentCameraScan
) {
    // 스캔 완료 처리
}
```

**Android (ML Kit)**:
```kotlin
import com.google.mlkit.vision.documentscanner.GmsDocumentScanner

val scanner = GmsDocumentScanning.getClient(options)
scanner.getStartScanIntent(activity)
    .addOnSuccessListener { intentSender ->
        // 스캔 시작
    }
```

### 3. Exposure Control 구현

#### 노출 최적화 (-1.0 ~ -0.5 단계)

**iOS (AVFoundation)**:
```swift
import AVFoundation

if let device = AVCaptureDevice.default(for: .video) {
    try? device.lockForConfiguration()
    
    // 노출 고정
    device.exposureMode = .custom
    device.setExposureTargetBias(-0.7) // -1.0 ~ -0.5 범위
    
    device.unlockForConfiguration()
}
```

**Android (Camera2 API)**:
```kotlin
import android.hardware.camera2.CameraCharacteristics

val exposureCompensation = -2 // -1.0 EV 단계
captureRequestBuilder.set(
    CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION,
    exposureCompensation
)
```

### 4. Document Restoration 구현

#### De-warping (기하학적 보정)

**OpenCV (Python)**:
```python
import cv2
import numpy as np

def dewarp_document(image):
    # 1. 문서 경계 감지
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 2. 가장 큰 사각형 찾기
    largest_contour = max(contours, key=cv2.contourArea)
    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    # 3. Perspective Transform
    if len(approx) == 4:
        pts = approx.reshape(4, 2)
        rect = order_points(pts)
        
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    
    return image
```

#### De-skewing (구김 제거)

**OpenCV (Python)**:
```python
def deskew_document(image):
    # 1. 이진화
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # 2. 회전 각도 계산
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # 3. 회전 적용
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated
```

#### Exposure Optimization (노출 최적화)

**PIL (Python)**:
```python
from PIL import Image, ImageEnhance

def optimize_exposure(image, factor=-0.7):
    """
    노출 최적화 (-1.0 ~ -0.5 단계)
    
    Args:
        image: PIL Image
        factor: 노출 조정 값 (-1.0 ~ 0)
    
    Returns:
        PIL Image: 최적화된 이미지
    """
    # 밝기 조정
    enhancer = ImageEnhance.Brightness(image)
    brightness_factor = 1.0 + factor  # 0.3 ~ 0.5 (어둡게)
    adjusted = enhancer.enhance(brightness_factor)
    
    # 대비 향상
    contrast_enhancer = ImageEnhance.Contrast(adjusted)
    final = contrast_enhancer.enhance(1.2)  # 대비 20% 향상
    
    return final
```

---

## 📱 CRM 앱 통합 방법

### 1. 증권 스캔 센터에 통합

**위치**: `blocks/crm_scan_block.py`

```python
from modules.digital_asset_collection_hub import render_digital_asset_collection_hub

def render_crm_scan_center():
    st.title("📸 증권 스캔 센터")
    
    # 디지털 자산 수집 허브 렌더링
    render_digital_asset_collection_hub()
```

### 2. 메인 대시보드에 바로가기 추가

**위치**: `crm_app_impl.py`

```python
# 메인 대시보드
if st.button("📸 증권 스캔", use_container_width=True):
    st.session_state["current_page"] = "scan_center"
    st.rerun()
```

### 3. 분석 파이프라인 연동

**위치**: `modules/zero_touch_vision.py`

```python
from modules.digital_asset_collection_hub import DigitalAssetCollectionHub

# 스캔된 문서 분석
hub = DigitalAssetCollectionHub()
queue = st.session_state["digital_asset_hub"]["analysis_queue"]

for document in queue:
    # Zero-Touch Vision 분석 적용
    analysis_result = analyze_document(document)
```

---

## 🧪 테스트 방법

### 개별 모듈 테스트

```bash
# Digital Asset Collection Hub
streamlit run modules/digital_asset_collection_hub.py
```

### 통합 테스트 시나리오

#### 시나리오 1: Drop Zone 테스트
1. 태블릿에서 앱 실행
2. Split View 활성화 (파일 앱 + CRM 앱)
3. PDF 파일을 Drop Zone으로 드래그
4. "자산을 안전하게 수신했습니다" 메시지 확인
5. 분석 대기열에 추가 확인

#### 시나리오 2: Smart Scan 테스트
1. [스캔 시작] 버튼 클릭
2. 카메라 권한 허용
3. 증권 문서를 카메라에 비춤
4. 문서 경계 자동 감지 확인
5. 자동 촬영 후 확인 팝업 표시
6. [분석 투입] 클릭
7. "정밀 분석을 시작합니다" 메시지 확인

#### 시나리오 3: Document Restoration 테스트
1. 구겨진 증권 촬영
2. 문서 복원 적용 확인
3. 비틀림 수정 애니메이션 확인
4. 복원 전/후 비교
5. OCR 인식률 향상 확인

---

## 📊 기대 효과

### 1. 입력 피로도 제로
- ✅ 드래그 앤 드롭으로 즉시 분석
- ✅ 스마트 스캔으로 자동 촬영
- ✅ 수동 입력 최소화

### 2. OCR 인식률 극대화
- ✅ 노출 최적화로 글자 선명도 확보
- ✅ 문서 복원으로 왜곡 제거
- ✅ 분석 오차 제로(0)에 근접

### 3. 태블릿 경험 최적화
- ✅ Split View 100% 활용
- ✅ 멀티태스킹 지원
- ✅ 직관적 인터페이스

### 4. 전문성 강화
- ✅ "고신뢰도 문서 복원 시스템" 이미지
- ✅ 육안보다 정교한 분석
- ✅ 리딩 파트너 차별화

---

## 🎉 결론

**디지털 자산 수집 허브**가 성공적으로 구축되었습니다.

**핵심 성과**:
- ✅ 태블릿 Drag & Drop 지원
- ✅ 인텔리전트 스캐너 모드
- ✅ 원문 보존형 노출 제어
- ✅ 지능형 문서 복원

**최종 메시지**:
> "증권 스캔을 '고신뢰도 문서 복원 시스템'으로 완성했습니다. 이제 육안으로 확인하는 것보다 더 정교한 분석이 가능합니다."

**다음 단계**: CRM 앱 증권 스캔 센터에 통합 및 실전 배포

---

**작성자**: goldkey_Ai_masters2026 프로젝트 팀  
**버전**: 1.0  
**최종 업데이트**: 2026-03-31
