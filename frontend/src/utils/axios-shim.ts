/**
 * Axios CDN Shim
 *
 * W1-D1 临时方案：axios 通过 index.html CDN 注入，window.axios 是全局对象
 * - 切回 npm 时，把 vite.config.ts 的 alias 'axios' 删掉即可
 */
declare global {
  interface Window {
    axios: any
  }
}

if (!window.axios) {
  console.error('[EVOLUTION AI] window.axios 不存在，CDN 未加载')
}

const axios = window.axios
export default axios
// 透传类型
export type AxiosInstance = any
export type AxiosError = any
export type AxiosRequestConfig = any
export type AxiosResponse = any
