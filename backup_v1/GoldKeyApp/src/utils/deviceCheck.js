/**
 * deviceCheck.js — 태블릿/폰 판별 + 레이아웃 상수
 * isTablet=true → 3-데크 가로 배치
 * isTablet=false → 세로 1컬럼 배치
 */
import { Dimensions, Platform } from 'react-native';

const { width, height } = Dimensions.get('window');
const shortEdge = Math.min(width, height);

export const isTablet = shortEdge >= 600;

export const LAYOUT = isTablet
  ? {
      sidebarWidth:  220,
      mainWidth:     width * 0.55,
      subWidth:      width * 0.25,
      contentPadding: 20,
    }
  : {
      sidebarWidth:  0,
      mainWidth:     width,
      subWidth:      width,
      contentPadding: 16,
    };
