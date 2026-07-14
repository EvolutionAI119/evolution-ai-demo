/**
 * Car Store（W2-D1 字段对齐）
 *
 * 状态：
 * - params: 当前 22 维参数（对齐 backend Pydantic）
 * - lastBuild: 最近一次 build_car 结果（GLB URL + stats）
 * - presets: 加载的预设
 * - loading: 构建中
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CarParamsAPI, CarBuildResponse, CarPresetsResponse } from '@/types/api'
import { buildCar, getCarPresets } from '@/api/car'

// 22 维默认参数（对齐 backend/models/car.py CarParamsAPI）
const DEFAULT_PARAMS: CarParamsAPI = {
  L: 4.7, W: 1.85, H: 1.45, wheelbase: 2.8,
  hood_length: 1.1, cabin_length: 2.2, trunk_length: 1.0, ground_clearance: 0.18,
  hood_angle: 12.0, roof_arc: 0.35, windshield_rake: 30.0, rear_glass_angle: 35.0,
  fender_prominence: 0.15, waist_line: 0.8, shoulder_line: 1.0, overall_arc: 0.2,
  glass_darkness: 0.4, wheel_radius: 0.34, wheel_width: 0.22, wheel_spoke_count: 5,
  headlight_width: 0.42, headlight_height: 0.10,
}

export const useCarStore = defineStore('car', () => {
  const params = ref<CarParamsAPI>({ ...DEFAULT_PARAMS })
  const lastBuild = ref<CarBuildResponse | null>(null)
  const presets = ref<Record<string, CarParamsAPI>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasBuild = computed(() => lastBuild.value !== null)
  const componentNames = computed(() =>
    lastBuild.value ? Object.keys(lastBuild.value.stats.components) : []
  )

  async function loadPresets(): Promise<void> {
    try {
      const resp: CarPresetsResponse = await getCarPresets()
      presets.value = resp.presets
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  async function build(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      lastBuild.value = await buildCar(params.value)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  function applyPreset(name: string): void {
    const p = presets.value[name]
    if (p) params.value = { ...p }
  }

  function resetParams(): void {
    params.value = { ...DEFAULT_PARAMS }
  }

  return {
    params,
    lastBuild,
    presets,
    loading,
    error,
    hasBuild,
    componentNames,
    loadPresets,
    build,
    applyPreset,
    resetParams,
  }
})
