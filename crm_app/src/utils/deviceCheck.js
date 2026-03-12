import { Platform, Dimensions, useWindowDimensions } from 'react-native';

const TABLET_MIN_WIDTH = 600;
const LEGACY_API_THRESHOLD = 28;

// ── 정적 isTablet / LAYOUT (컴포넌트 레벨에서 직접 사용) ─────────────────────
const _w = Dimensions.get('window').width;
export const isTablet = _w >= TABLET_MIN_WIDTH;
export const LAYOUT = {
  sidebarWidth: isTablet ? Math.floor(_w * 0.28) : 0,
  mainWidth:    isTablet ? Math.floor(_w * 0.44) : _w,
  subWidth:     isTablet ? Math.floor(_w * 0.28) : _w,
  padding:      isTablet ? 16 : 12,
};

export function getDeviceInfo() {
  const isAndroid = Platform.OS === 'android';
  const apiLevel = isAndroid ? (Platform.Version || 0) : 999;
  const isLegacyDevice = isAndroid && apiLevel < LEGACY_API_THRESHOLD;

  return { isLegacyDevice, apiLevel };
}

export function useDeviceLayout() {
  const { width } = useWindowDimensions();
  const isTablet = width >= TABLET_MIN_WIDTH;
  const { isLegacyDevice, apiLevel } = getDeviceInfo();

  return {
    isTablet,
    isLegacyDevice,
    apiLevel,
    numColumns: isTablet ? 2 : 1,
    contentPadding: isTablet ? 24 : 16,
    sidebarWidth: isTablet ? Math.floor(width * 0.38) : 0,
    mainWidth: isTablet ? Math.floor(width * 0.62) : width,
  };
}
