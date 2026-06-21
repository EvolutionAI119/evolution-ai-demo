/**
 * 21 端点 TypeScript 类型定义
 *
 * 字段命名严格对齐 backend Pydantic 模型（CarBuildResponse / OptimizeRequest / 等）
 * 涉及 ndarray 的字段（如 convergence_curve）约定为 number[]
 */
import type { TaskStatus } from './common'

// ==================== Car 模块 ====================

export interface CarParamsAPI {
  // 22 维参数（与 algorithm_model.CarParams 对齐）
  // 车身总体
  body_length: number
  body_width: number
  body_height: number
  wheelbase: number
  // 姿态
  ground_clearance: number
  approach_angle: number
  departure_angle: number
  // 比例
  overhang_front: number
  overhang_rear: number
  // 侧面轮廓
  beltline_height: number
  shoulder_line_angle: number
  // 表面曲率（设计师可调）
  hood_curvature: number
  fender_flare: number
  door_concavity: number
  // 玻璃
  windshield_angle: number
  rear_window_angle: number
  side_window_area: number
  // 轮拱
  wheel_arch_height: number
  wheel_arch_flare: number
  // 装饰
  character_lines: number
  overall_aggression: number
  // 类别预设
  category: 'sport' | 'luxury' | 'suv' | 'sedan' | 'custom'
}

export interface CarStatsAPI {
  // algorithm_model.compute_stats 返回字段
  num_panels: number
  total_vertices: number
  total_faces: number
  bounding_box: {
    min: [number, number, number]
    max: [number, number, number]
  }
  surface_area: number
  panel_names: string[]
}

export interface CarBuildResponse {
  glb_url: string  // 相对路径 /static/cars/xxx.glb
  stats: CarStatsAPI
  params_hash: string
  build_time_ms: number
}

export interface CarValidateResponse {
  valid: boolean
  errors: string[]
  warnings: string[]
}

export interface CarPresetsResponse {
  presets: Record<string, CarParamsAPI>
}

// ==================== Quality 模块 ====================

export interface QualityAssessRequest {
  // (N, M, 3) 三维点云展平为 (N*M, 3)
  points: number[][]
  panel_name: string
}

export interface QualityAssessResponse {
  panel_name: string
  g0_count: number
  g1_count: number
  g2_count: number
  g0_ratio: number
  g1_ratio: number
  g2_ratio: number
  grade: 'A' | 'B' | 'C' | 'D' | 'F'
  reflection_score: number
  mean_curvature: number
  max_curvature: number
  assess_time_ms: number
}

// ==================== Optimize 模块 ====================

export interface OptimizeRequest {
  points: number[][][]
  panel_name: string
  max_iter?: number
  seed?: number
}

export interface OptimizePresetRequest {
  shape: 'sphere' | 'plane' | 'cylinder' | 'car_body'
  max_iter?: number
  seed?: number
}

export interface OptimizeStartRequest {
  points: number[][][]
  panel_name: string
  max_iter?: number
  seed?: number
  project_id?: number
}

export interface OptimizeStartPresetRequest {
  shape: 'sphere' | 'plane' | 'cylinder' | 'car_body'
  max_iter?: number
  project_id?: number
}

export interface OptimizeStartResponse {
  task_id: string
  status: TaskStatus
  status_url: string
  panel_name?: string
  shape?: string
  max_iter: number
}

export interface OptimizeResult {
  initial_grade: string
  final_grade: string
  initial_g2: number
  final_g2: number
  initial_reflection: number
  final_reflection: number
  iterations: number
  convergence_curve: number[]
  elapsed_sec: number
  optimized_points?: number[][][]
}

// ==================== Storyboard 模块 ====================

export interface StoryboardMakeRequest {
  car_params: CarParamsAPI
  optimize_result?: OptimizeResult
  panels?: string[]
}

export interface StoryboardMakeResponse {
  storyboard_id: string
  scenes: Array<{
    index: number
    panel_name: string
    camera: {
      position: [number, number, number]
      target: [number, number, number]
      fov: number
    }
    duration_sec: number
    description: string
  }>
  total_duration_sec: number
}

export interface StoryboardRenderRequest {
  storyboard_id: string
  resolution?: [number, number]
  fps?: number
}

export interface StoryboardRenderResponse {
  video_url: string
  duration_sec: number
  file_size_mb: number
  render_time_sec: number
}

export interface StoryboardTemplatesResponse {
  templates: Array<{
    id: string
    name: string
    description: string
    default_panels: string[]
    camera_style: 'orbit' | 'flyby' | 'reveal' | 'dynamic'
  }>
}

// ==================== Project 模块 ====================

export interface ProjectCreateRequest {
  name: string
  description?: string
  tags?: string[]
  preset?: string
  params: CarParamsAPI
}

export interface Project {
  id: number
  name: string
  description: string
  tags: string
  preset: string
  params_json: string
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  total: number
  items: Project[]
  page: number
  page_size: number
}

export interface ProjectUpdateRequest {
  name?: string
  description?: string
  tags?: string[]
  preset?: string
  params?: CarParamsAPI
}

// ==================== Task 模块 ====================

export interface TaskInfo {
  task_id: string
  status: TaskStatus
  panel_name: string
  surface_type: string
  max_iter: number
  current_iter: number
  progress: number
  result_json?: string
  error_message?: string
  started_at?: string
  finished_at?: string
  created_at: string
  project_id?: number
}

export interface TaskListByProjectResponse {
  count: number
  items: TaskInfo[]
}

// ==================== Export 模块 ====================

export interface ExportGLBRequest {
  project_id: number
}

export interface ExportReportRequest {
  project_id: number
  format: 'pdf' | 'json' | 'html'
}
