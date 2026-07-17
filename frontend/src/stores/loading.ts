/**
 * 全局 loading 状态管理（W1-D2）
 *
 * 设计要点：
 * 1. 按 key（通常是 URL）维度去重计数：同一 URL 的并发请求只触发 1 次 loading
 * 2. 全局任意有 loading 时 → 全局 loadingStore.isLoading = true
 * 3. 不依赖具体业务组件，纯 Pinia store，axios 拦截器里 start/stop
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useLoadingStore = defineStore('loading', () => {
  // Map<key, count>：每个 key 当前在飞的请求数
  const inflight = ref<Record<string, number>>({})

  const isLoading = computed(() => {
    return Object.values(inflight.value).some((n) => n > 0)
  })

  const activeKeys = computed(() => {
    return Object.entries(inflight.value)
      .filter(([, n]) => n > 0)
      .map(([k]) => k)
  })

  function start(key: string) {
    inflight.value[key] = (inflight.value[key] ?? 0) + 1
  }

  function stop(key: string) {
    if (!inflight.value[key]) return
    inflight.value[key] -= 1
    if (inflight.value[key] <= 0) {
      delete inflight.value[key]
    }
  }

  function reset() {
    inflight.value = {}
  }

  return { inflight, isLoading, activeKeys, start, stop, reset }
})
