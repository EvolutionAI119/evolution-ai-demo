/**
 * Vue 3 应用入口（W2-D1 修复版：避免双 Vue 实例）
 *
 * M3 W1-D2: 集成 i18n (CDN 模式) + Pinia + Vue Router + Element Plus (CDN 模式)
 * 注意：Element Plus / Vue I18n / Axios 通过 index.html 里的 CDN 注入
 *  - 切回 npm 时，把 import 改回来即可
 *
 * D5 公网部署改造：
 *  - element-plus 整个 alias 到本地 shim（绕 ESM 循环依赖）
 *  - locale 文件从 element-plus 复制到本地 src/utils/element-plus-locales/
 *
 * W2-D1 修复：避免 vendor Vue + main.js 内联 Vue 双实例冲突
 *  - createApp/watch 全部走 window.Vue（vendor 单一实例）
 *  - main.js 不再 import 'vue'，避免 vite 把 Vue 运行时内联进 main.js
 */
import { createPinia } from 'pinia'
// D5 公网部署：locale 文件从 element-plus 复制到本地 src/utils/element-plus-locales/
// 绕开 element-plus npm 包内部 ESM 循环引用（runtime.mjs 引用 types.mjs 找不到）
import zhCn from './utils/element-plus-locales/zh-cn'

import App from './App.vue'
import router from './router'
import i18n from './i18n'

// 扩展 window 上的 CDN 全局对象类型
declare global {
  interface Window {
    Vue: any
    ElementPlus: any
    ElementPlusIconsVue: Record<string, any>
    vueI18n?: any
  }
}

// W2-D1 修复：用 vendor window.Vue（单一实例）而不是 import { createApp } from 'vue'
// 这样 element-plus UMD 用的 Vue 和我们 app 用的 Vue 是同一个实例
// 避免跨实例 useSlots 调 setupContext null 报错
const { createApp, watch } = window.Vue

const app = createApp(App)

// 注册所有 Element Plus 图标（CDN 注入到 window.ElementPlusIconsVue）
if (window.ElementPlusIconsVue) {
  for (const [key, component] of Object.entries(window.ElementPlusIconsVue)) {
    app.component(key, component)
  }
}

app.use(createPinia())
app.use(router)
app.use(i18n) // 必须在 router 之后、ElementPlus 之前

// 安装 Element Plus（CDN 加载后）
function installElementPlus() {
  if (window.ElementPlus) {
    app.use(window.ElementPlus, { locale: zhCn })
  } else {
    console.error('[EVOLUTION AI] Element Plus CDN 未加载，请检查网络')
  }
}

// 监听 i18n locale 变化 → 同步 document.documentElement.lang
watch(i18n.global.locale, (newLocale: string) => {
  document.documentElement.lang = newLocale
})

if (window.ElementPlus) {
  installElementPlus()
} else {
  document.addEventListener('DOMContentLoaded', installElementPlus)
}

app.mount('#app')
