/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'slide-speaker-main.onrender.com',
      'slide-speaker-main-1.onrender.com'
    ],
    // Proxy only for local Docker development (not in Render production)
    ...(process.env.NODE_ENV !== 'production' && !process.env.RENDER && {
      proxy: {
        '/api': {
          target: process.env.VITE_API_URL || 'http://backend:8000',
          changeOrigin: true,
          secure: false,
        }
      }
    })
  },
  preview: {
    allowedHosts: [
      'slide-speaker-main.onrender.com',
      'slide-speaker-main-1.onrender.com'
    ],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React core
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // TanStack Query
          'vendor-query': ['@tanstack/react-query'],
          // UI components
          'vendor-ui': [
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-select',
            '@radix-ui/react-toast',
            '@radix-ui/react-accordion',
            '@radix-ui/react-tabs',
            '@radix-ui/react-tooltip',
          ],
          // Utilities
          'vendor-utils': ['clsx', 'tailwind-merge', 'date-fns'],
          // Icons
          'vendor-icons': ['lucide-react'],
          // Charts
          'vendor-charts': ['chart.js', 'react-chartjs-2', 'recharts'],
          // Forms
          'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
    sourcemap: false, // Disable sourcemaps in production for smaller bundles
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/coverage/**',
        '**/dist/**',
        '**/.{idea,git,cache,output,temp}/**',
        '**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build}.config.*'
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})