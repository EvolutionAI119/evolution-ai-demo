/**
 * Car 模块：3 个端点
 * - POST /car/build       同步构车（5s+）
 * - POST /car/validate    参数校验
 * - GET  /car/presets     预设参数
 */
import http from './index'
import type { CarParamsAPI, CarBuildResponse, CarValidateResponse, CarPresetsResponse } from '@/types/api'

/** 同步构车（返回 GLB URL + stats） */
export async function buildCar(params: CarParamsAPI): Promise<CarBuildResponse> {
  const { data } = await http.post<CarBuildResponse>('/car/build', params)
  return data
}

/** 参数校验 */
export async function validateCar(params: CarParamsAPI): Promise<CarValidateResponse> {
  const { data } = await http.post<CarValidateResponse>('/car/validate', params)
  return data
}

/** 加载预设 */
export async function getCarPresets(): Promise<CarPresetsResponse> {
  const { data } = await http.get<CarPresetsResponse>('/car/presets')
  return data
}
