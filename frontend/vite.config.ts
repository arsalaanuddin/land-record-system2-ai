import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Host used for the cloud preview is supplied per process, never hardcoded.
    ...(process.env.VITE_DEV_ALLOWED_HOST ? { allowedHosts: [process.env.VITE_DEV_ALLOWED_HOST] } : {}),
    // Dev-only proxy so the browser talks to the API on the same origin.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
