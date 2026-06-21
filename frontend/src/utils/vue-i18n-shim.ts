// D5 公网部署：CDN 模式下 vue-i18n 走 window.__VUE_I18N__
// index.html 通过 CDN script 加载 vue-i18n@9 全局对象
type AnyFn = (...args: any[]) => any
const w: any = typeof window !== 'undefined' ? window : {}
const mod: any = w.__VUE_I18N__ || {}
export const createI18n: AnyFn = mod.createI18n || (() => ({}))
export const useI18n: AnyFn = mod.useI18n || (() => ({ t: (k: string) => k }))
export default mod.default || mod
