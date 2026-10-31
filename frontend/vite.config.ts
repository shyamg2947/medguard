import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/patients': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/review': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
      '/caregivers': 'http://localhost:8000',
      '/simulator': 'http://localhost:8000',
      '/share': 'http://localhost:8000',
      '/healthz': 'http://localhost:8000',
      '/readyz': 'http://localhost:8000',
    },
  },
});

