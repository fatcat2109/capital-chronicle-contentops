import React from 'react';
import ReactDOM from 'react-dom/client';
import '@fontsource/inter/400.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/800.css';
import '@fontsource/jetbrains-mono/500.css';
import '@fontsource/jetbrains-mono/700.css';
import './index.css';
import { DailyAppConsole } from './views/DailyAppConsole';
import { SimpleRunDashboard } from './views/SimpleRunDashboard';

const simpleView = new URLSearchParams(window.location.search).get('view') === 'simple';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    {simpleView ? <SimpleRunDashboard /> : <DailyAppConsole />}
  </React.StrictMode>,
);
