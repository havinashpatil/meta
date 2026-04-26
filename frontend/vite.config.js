import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/reset': { target: 'http://localhost:7860', changeOrigin: true },
      '/step':  { target: 'http://localhost:7860', changeOrigin: true },
      '/state': { target: 'http://localhost:7860', changeOrigin: true },
      '/health': { target: 'http://localhost:7860', changeOrigin: true },
      '/fix':   { target: 'http://localhost:7860', changeOrigin: true },
      '/run_raw': { target: 'http://localhost:7860', changeOrigin: true },
    },
  },
})
