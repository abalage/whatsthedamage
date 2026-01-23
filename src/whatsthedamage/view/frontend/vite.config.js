import { defineConfig } from 'vite';
import path from 'node:path';

export default defineConfig({
  root: path.resolve(__dirname, 'src'),
  build: {
    outDir: path.resolve(__dirname, '../static/dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'src/main.js'),
        index: path.resolve(__dirname, 'src/js/index.js'),
        apiDocs: path.resolve(__dirname, 'src/js/api-docs.js'),
        statisticalAnalysis: path.resolve(__dirname, 'src/js/statistical-analysis.js'),
        utils: path.resolve(__dirname, 'src/js/utils.js')
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
      '/api': 'http://localhost:5000',
      '/clear': 'http://localhost:5000',
      '/recalculate-statistics': 'http://localhost:5000'
    }
  }
});
