/**
 * Storyboard 模块：3 个端点
 * - POST /storyboard/make       生成脚本
 * - POST /storyboard/render     渲染视频
 * - GET  /storyboard/templates  模板列表
 */
import http from './index'
import type {
  StoryboardMakeRequest,
  StoryboardMakeResponse,
  StoryboardRenderRequest,
  StoryboardRenderResponse,
  StoryboardTemplatesResponse,
} from '@/types/api'

export async function makeStoryboard(req: StoryboardMakeRequest): Promise<StoryboardMakeResponse> {
  const { data } = await http.post<StoryboardMakeResponse>('/storyboard/make', req)
  return data
}

export async function renderStoryboard(req: StoryboardRenderRequest): Promise<StoryboardRenderResponse> {
  const { data } = await http.post<StoryboardRenderResponse>('/storyboard/render', req)
  return data
}

export async function getStoryboardTemplates(): Promise<StoryboardTemplatesResponse> {
  const { data } = await http.get<StoryboardTemplatesResponse>('/storyboard/templates')
  return data
}
