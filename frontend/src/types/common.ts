/**
 * 通用类型
 */
export type TaskStatus =
  | 'PENDING'
  | 'STARTED'
  | 'PROGRESS'
  | 'SUCCESS'
  | 'FAILURE'
  | 'REVOKED'

/** 优化任务 WebSocket 消息 */
export interface OptimizeWSMessage {
  type: TaskStatus
  progress: number  // 0-1
  current_iter: number
  max_iter: number
  best_score?: number
  elapsed_sec?: number
  initial_grade?: string
  final_grade?: string
  error?: string
  result?: Record<string, unknown>
}

/** 标准 API 错误响应 */
export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>
}
