import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const pyramidTarget = process.env.VITE_PYRAMID_API_ORIGIN || 'http://localhost:6543'
const fastApiTarget = process.env.VITE_FASTAPI_API_ORIGIN || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: pyramidTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ml-api': {
        target: fastApiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ml-api/, ''),
      },
    },
  },
})
