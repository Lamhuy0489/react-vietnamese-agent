import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '@fontsource/be-vietnam-pro/400.css';
import '@fontsource/be-vietnam-pro/500.css';
import '@fontsource/be-vietnam-pro/600.css';
import '@fontsource/jetbrains-mono/400.css';
import './theme/tokens.css';
import './theme/base.css';
import { App } from './App';

const container = document.getElementById('root');

if (!container) {
  throw new Error('Không tìm thấy phần tử gốc #root');
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
