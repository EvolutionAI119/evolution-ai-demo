/**
 * i18n 配置
 *
 * - 自动检测浏览器语言：navigator.language 是 en-* → en-US，否则 zh-CN
 * - localStorage 记忆用户手动切换：localStorage.lang
 * - 全局变量 window.__VUE_I18N__（CDN 模式从 jsdelivr 加载）
 */
import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'

export type Locale = 'zh-CN' | 'en-US'
export const SUPPORTED_LOCALES: Locale[] = ['zh-CN', 'en-US']
export const LOCALE_STORAGE_KEY = 'evolution_ai_lang'

/**
 * 解析浏览器/本地存储语言偏好
 * 优先级：localStorage > navigator.language > zh-CN（默认）
 */
function resolveLocale(): Locale {
  try {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (stored === 'zh-CN' || stored === 'en-US') return stored
  } catch {
    // localStorage 在 SSR / 隐私模式可能不可用
  }
  const nav = (navigator?.language || 'zh-CN').toLowerCase()
  if (nav.startsWith('en')) return 'en-US'
  return 'zh-CN'
}

export const i18n = createI18n({
  legacy: false, // 用 Composition API
  globalInjection: true,
  locale: resolveLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})

/**
 * 切换语言并持久化
 */
export function setLocale(locale: Locale) {
  i18n.global.locale.value = locale
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // 忽略存储失败
  }
  document.documentElement.lang = locale
}

export default i18n
