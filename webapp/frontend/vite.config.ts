import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev server proxies the API to the FastAPI backend (uvicorn on 127.0.0.1:8000).
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } },
  },
  build: { outDir: 'dist', emptyOutDir: true, sourcemap: false },
})
