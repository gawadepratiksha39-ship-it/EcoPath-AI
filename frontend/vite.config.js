/**
 * vite.config.js — Vite build tool configuration.
 *
 * Proxies /api requests to the Flask backend during development
 * so the frontend can call the API without CORS issues.
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
