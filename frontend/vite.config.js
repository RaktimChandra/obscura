import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { // dev proxy so the app calls the backend without CORS friction
      '/api': { target: 'http://localhost:8080', changeOrigin: true,
                rewrite: p => p.replace(/^\/api/, '') }
    }
  }
})
