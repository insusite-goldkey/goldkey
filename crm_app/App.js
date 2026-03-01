/**
 * 골드키 CRM 앱 진입점 (App.js)
 * React Native CLI 기준
 */

import React from 'react';
import { StatusBar } from 'react-native';
import Dashboard from './src/screens/Dashboard';

const App = () => (
  <>
    <StatusBar barStyle="light-content" backgroundColor="#1e3a5f" />
    <Dashboard />
  </>
);

export default App;
