/**
 * Optimize 模块：4 个端点
 * - POST /optimize/run            同步（M1 兼容）
 * - POST /optimize/run-preset     同步（M1 兼容）
 * - POST /optimize/start          异步（M2）
 * - POST /optimize/start-preset   异步（M2 + M2.5 WS）
 */
import http from './index'
import type {
  OptimizeRequest,
  OptimizePresetRequest,
  OptimizeStartRequest,
  OptimizeStartPresetRequest,
  OptimizeStartResponse,
  OptimizeResult,
} from '@/types/api'

export async function optimizeSync(req: OptimizeRequest): Promise<OptimizeResult> {
  const { data } = await http.post<OptimizeResult>('/optimize/run', req)
  return data
}

export async function optimizePresetSync(req: OptimizePresetRequest): Promise<OptimizeResult> {
  const { data } = await http.post<OptimizeResult>('/optimize/run-preset', req)
  return data
}

export async function optimizeStart(req: OptimizeStartRequest): Promise<OptimizeStartResponse> {
  const { data } = await http.post<OptimizeStartResponse>('/optimize/start', req)
  return data
}

export async function optimizeStartPreset(req: OptimizeStartPresetRequest): Promise<OptimizeStartResponse> {
  const { data } = await http.post<OptimizeStartResponse>('/optimize/start-preset', req)
  return data
}

/** WebSocket URL（M2.5） */
export function wsOptimizeUrl(taskId: string): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/api/v1/ws/optimize/${taskId}`
}
