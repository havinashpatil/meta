import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxy OpenEnv FastAPI calls → avoids CORS
      '/reset': { target: 'http://localhost:7860', changeOrigin: true },
      '/step':  { target: 'http://localhost:7860', changeOrigin: true },
      '/state': { target: 'http://localhost:7860', changeOrigin: true },
    },
  },
})
