/**
 * Quality 模块：1 个端点
 * - POST /quality/assess  同步曲面质量评估
 */
import http from './index'
import type { QualityAssessRequest, QualityAssessResponse } from '@/types/api'

export async function assessQuality(req: QualityAssessRequest): Promise<QualityAssessResponse> {
  const { data } = await http.post<QualityAssessResponse>('/quality/assess', req)
  return data
}
