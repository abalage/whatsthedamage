import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'node:path';

export default defineConfig({
  root: path.resolve(__dirname, '.'),
  base: '/',
  publicDir: path.resolve(__dirname, 'public'),
  plugins: [
    vue()
  ],
  build: {
    outDir: path.resolve(__dirname, 'dist'),
    emptyOutDir: true,
    cssCodeSplit: true,
    minify: 'terser',
    sourcemap: true,
    chunkSizeWarningLimit: 500,
    copyPublicDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html')

      },
      output: {
        entryFileNames: 'js/[name].js',
        chunkFileNames: 'js/[name].js',
        assetFileNames: 'css/[name].[ext]'
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api/v2': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
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