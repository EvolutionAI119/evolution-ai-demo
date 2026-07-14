// D5 公网部署：CDN 模式下 element-plus 不走 npm
// index.html 已通过 <script> 全局引入 window.ElementPlus
// 这里从 window 兜底导出 named exports，避免 vite build 时卷入 element-plus ESM
type AnyFn = (...args: any[]) => any
const w: any = typeof window !== 'undefined' ? window : {}
const ep: any = w.ElementPlus || {}

export const ElMessage: AnyFn = ep.ElMessage || (() => {})
export const ElMessageBox: AnyFn = ep.ElMessageBox || (() => {})
export const ElNotification: AnyFn = ep.ElNotification || (() => {})
export const ElMessageType: any = ep.ElMessageType || {}
export const ElMessageBoxType: any = ep.ElMessageBoxType || {}

// 兜底空对象，防止 import * as EP 报 undefined
const ElementPlus = ep
export default ElementPlus
