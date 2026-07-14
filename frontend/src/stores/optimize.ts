/**
 * Optimize Store（M3 W1-D1 骨架）
 *
 * 状态：
 * - currentTask: 当前任务（task_id + status + progress + current_iter + result）
 * - ws: WebSocket 实例
 * - history: 历史任务列表
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { OptimizeStartResponse, OptimizeResult } from '@/types/api'
import type { TaskStatus, OptimizeWSMessage } from '@/types/common'
import { optimizeStartPreset, wsOptimizeUrl } from '@/api/optimize'

export const useOptimizeStore = defineStore('optimize', () => {
  const currentTaskId = ref<string | null>(null)
  const currentStatus = ref<TaskStatus | null>(null)
  const progress = ref(0)
  const currentIter = ref(0)
  const maxIter = ref(30)
  const bestScore = ref<number | null>(null)
  const result = ref<OptimizeResult | null>(null)
  const error = ref<string | null>(null)

  let ws: WebSocket | null = null

  const isRunning = computed(
    () => currentStatus.value === 'PENDING' || currentStatus.value === 'STARTED' || currentStatus.value === 'PROGRESS',
  )
  const isDone = computed(() => currentStatus.value === 'SUCCESS' || currentStatus.value === 'FAILURE')

  function reset(): void {
    currentTaskId.value = null
    currentStatus.value = null
    progress.value = 0
    currentIter.value = 0
    maxIter.value = 30
    bestScore.value = null
    result.value = null
    error.value = null
  }

  function disconnect(): void {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  async function startPreset(shape: 'sphere' | 'plane' | 'cylinder' | 'car_body', iter = 30): Promise<void> {
    reset()
    maxIter.value = iter
    try {
      const resp: OptimizeStartResponse = await optimizeStartPreset({ shape, max_iter: iter })
      currentTaskId.value = resp.task_id
      currentStatus.value = resp.status
      connectWS(resp.task_id)
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  function connectWS(taskId: string): void {
    disconnect()
    const url = wsOptimizeUrl(taskId)
    ws = new WebSocket(url)
    ws.onmessage = (ev: MessageEvent) => {
      try {
        const msg: OptimizeWSMessage = JSON.parse(ev.data)
        currentStatus.value = msg.type
        progress.value = msg.progress
        currentIter.value = msg.current_iter
        maxIter.value = msg.max_iter
        if (msg.best_score !== undefined) bestScore.value = msg.best_score
        if (msg.type === 'SUCCESS' && msg.result) {
          result.value = msg.result as unknown as OptimizeResult
        }
        if (msg.type === 'FAILURE' && msg.error) {
          error.value = msg.error
        }
        if (msg.type === 'SUCCESS' || msg.type === 'FAILURE') {
          disconnect()
        }
      } catch (e) {
        error.value = (e as Error).message
      }
    }
    ws.onerror = () => {
      error.value = 'WebSocket 连接失败'
    }
  }

  return {
    currentTaskId,
    currentStatus,
    progress,
    currentIter,
    maxIter,
    bestScore,
    result,
    error,
    isRunning,
    isDone,
    startPreset,
    disconnect,
    reset,
  }
})
