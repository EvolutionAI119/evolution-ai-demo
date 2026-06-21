import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { resolve as pathResolve } from 'node:path'

export default defineConfig({
  base: '/evolution-ai-demo/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'vue': pathResolve(
        fileURLToPath(new URL('./node_modules/vue/dist/vue.esm-bundler.js', import.meta.url))
      ),
      'axios': fileURLToPath(new URL('./src/utils/axios-shim.ts', import.meta.url)),
      'element-plus/es': fileURLToPath(new URL('./src/utils/element-plus-shim.ts', import.meta.url)),
      'element-plus': fileURLToPath(new URL('./src/utils/element-plus-shim.ts', import.meta.url)),
      'vue-i18n': fileURLToPath(new URL('./src/utils/vue-i18n-shim.ts', import.meta.url)),
    },
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia'],
    exclude: ['axios', 'element-plus', 'vue-i18n'],
    esbuildOptions: { sourcemap: false },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, ws: true },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    target: 'es2022',
    commonjsOptions: { include: [/.+/], transformMixedEsModules: true },
  },
})
