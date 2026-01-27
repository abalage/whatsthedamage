import { defineConfig } from 'vite';
import path from 'node:path';

export default defineConfig({
  root: path.resolve(__dirname, 'src'),
  base: '/static/dist/',
  build: {
    outDir: path.resolve(__dirname, '../static/dist'),
    emptyOutDir: true,
    cssCodeSplit: true,
    minify: 'terser',
    sourcemap: true,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'src/main.ts'),
        index: path.resolve(__dirname, 'src/js/index.ts'),
        statisticalAnalysis: path.resolve(__dirname, 'src/js/statistical-analysis.ts'),
        utils: path.resolve(__dirname, 'src/js/utils.ts'),
        api: path.resolve(__dirname, 'src/js/api.ts')
      },
      output: {
        entryFileNames: 'js/[name].js',
        chunkFileNames: 'js/[name].js',
        assetFileNames: 'css/[name].[ext]',
        manualChunks: {
          vendor: ['jquery', 'bootstrap', 'datatables.net']
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:5000',
      '/clear': 'http://localhost:5000',
      '/recalculate-statistics': 'http://localhost:5000'
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['../test/**/*.{test,spec}.?(c|m)[jt]s?(x)'],
    setupFiles: '../test/setup.js',
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'dist/', 'coverage/']
    }
  }
});