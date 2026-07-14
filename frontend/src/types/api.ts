/**
 * 21 端点 TypeScript 类型定义
 *
 * 字段命名严格对齐 backend Pydantic 模型（CarBuildResponse / OptimizeRequest / 等）
 * 涉及 ndarray 的字段（如 convergence_curve）约定为 number[]
 */
import type { TaskStatus } from './common'

// ==================== Car 模块 ====================

export interface CarParamsAPI {
  // 22 维参数（严格对齐 backend/models/car.py CarParamsAPI Pydantic 字段）
  // W2-D1 修复：之前字段名（body_length/...）和后端 Pydantic (L/W/H/...) 不一致，
  //           导致 /car/build 接口永远走默认值；现统一用后端字段名
  // 基础尺寸
  L: number             // 车长 m (3.5-5.5)
  W: number             // 车宽 m (1.6-2.1)
  H: number             // 车高 m (1.25-1.85)
  wheelbase: number     // 轴距 m (2.3-3.2)
  // 比例姿态
  hood_length: number   // 发动机盖长 m (0.7-1.5)
  cabin_length: number  // 座舱长 m (1.6-2.6)
  trunk_length: number  // 行李箱长 m (0.5-1.4)
  ground_clearance: number  // 离地间隙 m (0.12-0.25)
  // 曲面特征
  hood_angle: number    // 发动机盖角度 ° (5-25)
  roof_arc: number      // 车顶弧度 (0-0.8)
  windshield_rake: number  // 前挡风倾角 ° (20-40)
  rear_glass_angle: number  // 后挡风倾角 ° (25-45)
  fender_prominence: number  // 轮眉突出 (0-0.35)
  waist_line: number    // 腰线高度比 (0.65-0.95)
  shoulder_line: number // 肩线高度比 (0.85-1.15)
  // 整体
  overall_arc: number   // 整体弧度 (0-0.7)
  // 玻璃
  glass_darkness: number  // 玻璃透射 (0.1-0.7)
  // 轮
  wheel_radius: number  // 轮半径 m (0.28-0.40)
  wheel_width: number   // 轮宽 m (0.18-0.28)
  wheel_spoke_count: number  // 辐条数 (3-10)
  // 灯
  headlight_width: number   // 大灯宽度 m (0.30-0.55)
  headlight_height: number  // 大灯高度 m (0.06-0.16)
}

export interface CarStatsAPI {
  // 对齐 backend.models.car.CarStatsAPI Pydantic
  total_vertices: number
  total_faces: number
  components: Record<string, { vertices: number; faces: number; color: string }>  // {part_name: {...}}
  bounds: [[number, number, number], [number, number, number]]  // [[min], [max]]
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
