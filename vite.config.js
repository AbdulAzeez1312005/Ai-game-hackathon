import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const projectRoot = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  root: projectRoot,
  plugins: [react()],
  build: {
    outDir: fileURLToPath(new URL('./static/dist/', import.meta.url)),
    emptyOutDir: true,
    assetsDir: '',
    rollupOptions: {
      input: fileURLToPath(new URL('./frontend/src/main.jsx', import.meta.url)),
      output: {
        entryFileNames: 'app.js',
        assetFileNames: '[name][extname]',
      },
    },
  },
});
