/**
 * Axios 客户端（W1-D2 增强）
 *
 * 职责：
 * 1. 实例化 axios（baseURL / timeout / headers）
 * 2. 请求拦截器：注入 token + 启动 loading
 * 3. 响应拦截器：成功 → 解 data / 失败 → 归一化 8 case → 弹 ElMessage → 联动 loading
 * 4. 与 Pinia loading store 联动（按 url 维度去重计数）
 */
import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

import { normalizeError, type NormalizedError } from '@/utils/error'
import { useLoadingStore } from '@/stores/loading'

declare module 'axios' {
  export interface AxiosRequestConfig {
    /** 跳过全局 loading（用于高频轮询 / WebSocket 心跳） */
    skipLoading?: boolean
  }
  export interface AxiosRequestConfig__Custom {
    // 占位：未来如果需要扩展自定义配置可放这里
  }
}

const http: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ============== 请求拦截器 ==============
http.interceptors.request.use(
  (config) => {
    // 1. 注入 token（如果有）
    try {
      const token = localStorage.getItem('evolution_ai_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch {
      // 忽略 localStorage 不可用
    }

    // 2. 启动 loading（按 url 维度去重）
    if (!config.skipLoading) {
      try {
        const loadingStore = useLoadingStore()
        const key = config.url || 'unknown'
        loadingStore.start(key)
      } catch {
        // Pinia 还未安装（SSR / 测试场景）—— 静默忽略
      }
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ============== 响应拦截器 ==============
http.interceptors.response.use(
  (response: AxiosResponse) => {
    // 关闭 loading
    if (!response.config.skipLoading) {
      try {
        const loadingStore = useLoadingStore()
        const key = response.config.url || 'unknown'
        loadingStore.stop(key)
      } catch {
        // ignore
      }
    }
    return response
  },
  (error) => {
    // 关闭 loading（异常也算）
    const url = error.config?.url || 'unknown'
    if (!error.config?.skipLoading) {
      try {
        const loadingStore = useLoadingStore()
        loadingStore.stop(url)
      } catch {
        // ignore
      }
    }

    // 归一化错误 → 弹错
    const normalized: NormalizedError = normalizeError(error)
    // 业务约定：401 静默（待接入登录页），其它 case 提示
    if (normalized.code !== 401) {
      ElMessage({
        message: normalized.message,
        type: normalized.type,
        duration: normalized.type === 'error' ? 4000 : 2000,
      })
    }
    return Promise.reject(normalized)
  },
)

export default http
export type { AxiosRequestConfig }
