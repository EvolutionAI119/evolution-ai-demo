/**
 * 错误归一化工具
 *
 * 把 axios 抛出的任何错误（4xx / 5xx / 网络 / 超时 / 业务 / 未知）
 * 归一化成 NormalizedError，方便上层统一处理 + i18n 提示
 *
 * 覆盖 8 个 case：
 *  1. 网络错误（无 response）
 *  2. 请求超时（ECONNABORTED）
 *  3. 4xx 客户端错误（含 401 未授权 / 404 找不到 / 422 校验失败）
 *  4. 5xx 服务端错误
 *  5. 业务错误（后端约定的 200 + error_code 非 0）
 *  6. WebSocket 握手错误
 *  7. JSON 解析错误
 *  8. 未知错误
 */
import type { AxiosError } from 'axios'
import type { MessageType } from 'element-plus'

export interface NormalizedError {
  /** 错误类型，用于 ElMessage.type */
  type: MessageType
  /** 用户可读消息（已经过 i18n 化的 key 或回退字符串） */
  message: string
  /** 数字错误码（HTTP status 或业务 code） */
  code: number | string
  /** 原始 axios 错误，方便排查 */
  raw?: AxiosError
}

interface AxiosErrorResponse {
  detail?: string | { msg?: string; message?: string } | unknown
  message?: string
  error_code?: number
  code?: number
}

/**
 * 归一化错误入口
 */
export function normalizeError(err: unknown): NormalizedError {
  // 已经是 NormalizedError 直接返回（拦截器内防止重复包装）
  if (err && typeof err === 'object' && 'type' in err && 'code' in err && 'message' in err) {
    return err as NormalizedError
  }

  // axios error
  if (isAxiosError(err)) {
    const ax = err as AxiosError<AxiosErrorResponse>
    // case 7: JSON 解析错误
    if (ax.code === 'ERR_BAD_RESPONSE' || /JSON/.test(ax.message)) {
      return {
        type: 'error',
        message: '服务器返回数据格式错误',
        code: 'PARSE_ERROR',
        raw: ax,
      }
    }
    // case 2: 超时
    if (ax.code === 'ECONNABORTED' || ax.message.includes('timeout')) {
      return {
        type: 'warning',
        message: '请求超时，请稍后重试',
        code: 'TIMEOUT',
        raw: ax,
      }
    }
    // 有 HTTP 响应 → 3xx/4xx/5xx
    if (ax.response) {
      const status = ax.response.status
      const data = ax.response.data
      const detail = data?.detail
      const detailStr = extractDetail(detail) || data?.message || ax.message
      if (status >= 500) {
        // case 4: 5xx
        return { type: 'error', message: `服务器错误 (${status}): ${detailStr}`, code: status, raw: ax }
      }
      if (status >= 400) {
        // case 3: 4xx
        return { type: 'error', message: `请求错误 (${status}): ${detailStr}`, code: status, raw: ax }
      }
    }
    // case 1: 网络错误（无 response）
    return {
      type: 'error',
      message: '网络错误，请检查连接',
      code: 'NETWORK_ERROR',
      raw: ax,
    }
  }

  // 普通 Error
  if (err instanceof Error) {
    return { type: 'error', message: err.message || '未知错误', code: 'UNKNOWN', raw: undefined }
  }

  // case 8: 完全未知
  return { type: 'error', message: '未知错误', code: 'UNKNOWN', raw: undefined }
}

function isAxiosError(err: unknown): err is AxiosError {
  return !!err && typeof err === 'object' && 'isAxiosError' in err && (err as any).isAxiosError === true
}

function extractDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object') {
    const d = detail as { msg?: string; message?: string }
    return d.msg || d.message || JSON.stringify(detail)
  }
  return ''
}
