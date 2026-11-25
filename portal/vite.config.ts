import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Em desenvolvimento o Vite faz o papel do Nginx: mesmas rotas /api, sem o prefixo.
const semApi = (p: string) => p.replace(/^\/api/, '');
const clinical = `http://127.0.0.1:${process.env.CLINICAL_PORT ?? 8080}`;
const documento = `http://127.0.0.1:${process.env.DOCUMENT_PORT ?? 8000}`;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api/auth': { target: 'http://127.0.0.1:3001', rewrite: semApi },
      '/api/profissional': { target: 'http://127.0.0.1:3001', rewrite: semApi },
      '/api/documento': { target: documento, rewrite: semApi },
      '/api': { target: clinical, rewrite: semApi },
    },
  },
});
