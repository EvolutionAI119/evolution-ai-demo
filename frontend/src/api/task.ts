/**
 * Task 模块：2 个端点
 * - GET /task/{task_id}            查任务状态
 * - GET /task/by-project/{project_id}  查某方案下的所有任务
 */
import http from './index'
import type { TaskInfo, TaskListByProjectResponse } from '@/types/api'

export async function getTask(taskId: string): Promise<TaskInfo> {
  const { data } = await http.get<TaskInfo>(`/task/${taskId}`)
  return data
}

export async function listTasksByProject(projectId: number): Promise<TaskListByProjectResponse> {
  const { data } = await http.get<TaskListByProjectResponse>(`/task/by-project/${projectId}`)
  return data
}
