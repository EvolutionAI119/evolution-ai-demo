/**
 * Car Store（M3 W1-D1 骨架）
 *
 * 状态：
 * - params: 当前 22 维参数
 * - lastBuild: 最近一次 build_car 结果（GLB URL + stats）
 * - presets: 加载的预设
 * - loading: 构建中
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CarParamsAPI, CarBuildResponse, CarPresetsResponse } from '@/types/api'
import { buildCar, getCarPresets } from '@/api/car'

const DEFAULT_PARAMS: CarParamsAPI = {
  body_length: 4.7,
  body_width: 1.85,
  body_height: 1.45,
  wheelbase: 2.8,
  ground_clearance: 0.18,
  approach_angle: 16,
  departure_angle: 22,
  overhang_front: 0.95,
  overhang_rear: 1.05,
  beltline_height: 0.95,
  shoulder_line_angle: 8,
  hood_curvature: 0.05,
  fender_flare: 0.12,
  door_concavity: 0.02,
  windshield_angle: 28,
  rear_window_angle: 35,
  side_window_area: 0.35,
  wheel_arch_height: 0.4,
  wheel_arch_flare: 0.08,
  character_lines: 3,
  overall_aggression: 0.5,
  category: 'sedan',
}

export const useCarStore = defineStore('car', () => {
  const params = ref<CarParamsAPI>({ ...DEFAULT_PARAMS })
  const lastBuild = ref<CarBuildResponse | null>(null)
  const presets = ref<Record<string, CarParamsAPI>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasBuild = computed(() => lastBuild.value !== null)
  const panelNames = computed(() => lastBuild.value?.stats.panel_names ?? [])

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

  function applyPreset(name: keyof typeof DEFAULT_PARAMS | string): void {
    const p = presets.value[name as string]
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
    panelNames,
    loadPresets,
    build,
    applyPreset,
    resetParams,
  }
})
