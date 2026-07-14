import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
import { resolve as pathResolve } from 'node:path';
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
            'vue': pathResolve(fileURLToPath(new URL('./node_modules/vue/dist/vue.esm-bundler.js', import.meta.url))),
            'axios': fileURLToPath(new URL('./src/utils/axios-shim.ts', import.meta.url)),
            // D5 公网部署：所有 element-plus 引用（含子路径）都走 shim
            // 反正代码里只剩 locale import（main.ts 已改本地），其他用 named export 也走 shim
            'element-plus/es': fileURLToPath(new URL('./src/utils/element-plus-shim.ts', import.meta.url)),
            'element-plus': fileURLToPath(new URL('./src/utils/element-plus-shim.ts', import.meta.url)),
        },
    },
    optimizeDeps: {
        include: ['vue', 'vue-router', 'pinia'],
        exclude: ['axios', 'element-plus'],
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
});
