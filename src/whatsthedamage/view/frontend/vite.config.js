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
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'src/main.js'),
        index: path.resolve(__dirname, 'src/js/index.js'),
        apiDocs: path.resolve(__dirname, 'src/js/api-docs.js'),
        statisticalAnalysis: path.resolve(__dirname, 'src/js/statistical-analysis.js'),
        utils: path.resolve(__dirname, 'src/js/utils.ts')
      },
      output: {
        entryFileNames: 'js/[name].js',
        chunkFileNames: 'js/[name].js',
        assetFileNames: 'css/[name].[ext]',
        manualChunks: {
          vendor: ['jquery', 'bootstrap', 'datatables.net'],
          swagger: ['swagger-ui-dist']
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
    include: ['**/*.{test,spec}.?(c|m)[jt]s?(x)'],
    setupFiles: './test/setup.js',
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'dist/', 'coverage/']
    }
  }
});