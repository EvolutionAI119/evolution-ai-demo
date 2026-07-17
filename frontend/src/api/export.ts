/**
 * Export 模块：3 个端点
 * - POST /export/glb       导出 GLB 文件
 * - POST /export/report    导出报告（pdf/json/html）
 * - GET  /export/formats   支持的格式列表
 */
import http from './index'
import type { ExportGLBRequest, ExportReportRequest } from '@/types/api'

export async function exportGLB(req: ExportGLBRequest): Promise<Blob> {
  const { data } = await http.post<Blob>('/export/glb', req, { responseType: 'blob' })
  return data
}

export async function exportReport(req: ExportReportRequest): Promise<Blob> {
  const { data } = await http.post<Blob>('/export/report', req, { responseType: 'blob' })
  return data
}

export async function getExportFormats(): Promise<{ formats: string[] }> {
  const { data } = await http.get<{ formats: string[] }>('/export/formats')
  return data
}
