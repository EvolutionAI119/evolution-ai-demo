/**
 * Axios 客户端 + 21 端点封装（W1-D2 调整）
 *
 * 端点命名按模块分文件：car.ts / quality.ts / optimize.ts / storyboard.ts / project.ts / task.ts / export.ts
 * 统一走 /api/v1 前缀
 *
 * 实例化逻辑搬到了 ./client.ts（拦截器 + 错误归一 + loading 联动）
 * 本文件只做 re-export 各业务模块
 */
import http from './client'
export default http

export * from './car'
export * from './quality'
export * from './optimize'
export * from './storyboard'
export * from './project'
export * from './task'
export * from './export'
