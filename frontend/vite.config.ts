import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  // .env лежит в корне репозитория (общий для backend и frontend). Только
  // переменные с префиксом VITE_ попадают в клиентский бандл.
  envDir: '..',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
