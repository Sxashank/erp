/// <reference types="vitest" />
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5176,
  },
  build: {
    // Vendor chunking — keeps a stable long-cached bundle per dep. Tuned for
    // the SMFC ERP payload: react + router + tanstack-query hot-load on every
    // page; recharts + pdf/excel only load on report screens.
    // See STAGE-8-PENDING-bundle-chunking closure.
    rollupOptions: {
      output: {
        manualChunks: (id: string) => {
          if (!id.includes('node_modules')) return undefined;
          if (id.includes('/recharts/')) return 'vendor-charts';
          if (id.includes('/jspdf/') || id.includes('/html2canvas/') || id.includes('/dompurify/')) {
            return 'vendor-pdf';
          }
          if (id.includes('/exceljs/')) return 'vendor-excel';
          if (id.includes('/react/') || id.includes('/react-dom/') || id.includes('/scheduler/')) {
            return 'vendor-react';
          }
          if (id.includes('/@tanstack/react-query/') || id.includes('/zustand/')) {
            return 'vendor-state';
          }
          if (id.includes('/@radix-ui/')) return 'vendor-radix';
          if (id.includes('/react-hook-form/') || id.includes('/zod/')) {
            return 'vendor-forms';
          }
          if (id.includes('/react-router-dom/') || id.includes('/react-router/')) {
            return 'vendor-router';
          }
          if (id.includes('/lucide-react/')) return 'vendor-icons';
          return 'vendor-other';
        },
      },
    },
    // Raise the warning bar — we've already split vendors. Individual route
    // chunks under 500 kB are fine; the main entry under 300 kB is ideal.
    chunkSizeWarningLimit: 700,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/**',
        'dist/**',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.int.test.{ts,tsx}',
        'src/**/*.d.ts',
        'src/test/**',
        'src/main.tsx',
        'src/App.tsx',
      ],
    },
  },
});
