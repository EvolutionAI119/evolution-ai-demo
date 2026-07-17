/**
 * Project 模块：5 个端点
 * - POST   /project/        创建
 * - GET    /project/        列表
 * - GET    /project/{id}    详情
 * - PUT    /project/{id}    更新
 * - DELETE /project/{id}    删除
 */
import http from './index'
import type {
  ProjectCreateRequest,
  ProjectUpdateRequest,
  Project,
  ProjectListResponse,
} from '@/types/api'

export async function createProject(req: ProjectCreateRequest): Promise<Project> {
  const { data } = await http.post<Project>('/project/', req)
  return data
}

export async function listProjects(page = 1, pageSize = 20): Promise<ProjectListResponse> {
  const { data } = await http.get<ProjectListResponse>('/project/', { params: { page, page_size: pageSize } })
  return data
}

export async function getProject(id: number): Promise<Project> {
  const { data } = await http.get<Project>(`/project/${id}`)
  return data
}

export async function updateProject(id: number, req: ProjectUpdateRequest): Promise<Project> {
  const { data } = await http.put<Project>(`/project/${id}`, req)
  return data
}

export async function deleteProject(id: number): Promise<void> {
  await http.delete(`/project/${id}`)
}
