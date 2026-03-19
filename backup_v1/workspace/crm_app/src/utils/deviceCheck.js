import { Platform, useWindowDimensions } from 'react-native';

const TABLET_MIN_WIDTH = 600;
const LEGACY_API_THRESHOLD = 28;

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
