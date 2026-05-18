/// <reference types="vitest" />
import path from 'path';

import react from '@vitejs/plugin-react';
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
          if (
            id.includes('/react/') ||
            id.includes('/react-dom/') ||
            id.includes('/scheduler/') ||
            id.includes('/react-router-dom/') ||
            id.includes('/react-router/') ||
            id.includes('/@tanstack/react-query/') ||
            id.includes('/zustand/') ||
            id.includes('/@radix-ui/') ||
            id.includes('/react-hook-form/') ||
            id.includes('/zod/')
          ) {
            return 'vendor-ui-core';
          }
          if (id.includes('/lucide-react/')) return 'vendor-icons';
          return 'vendor-ui-core';
        },
      },
    },
    // The admin route registry intentionally carries the enterprise module map.
    // Heavier report-only vendors stay split above, so keep warnings for >1.1 MB.
    chunkSizeWarningLimit: 1100,
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
