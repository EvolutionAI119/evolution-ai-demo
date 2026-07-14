<script setup lang="ts">
/**
 * 造型设计页面（W2-D1 - 真实 NURBS 曲面渲染）
 *
 * 闭环：22 维参数滑块 → 防抖 400ms → POST /api/v1/car/build →
 *      拿 glb_url → Three.js GLTFLoader 加载 → 场景渲染
 *
 * 关键修复（W2-D1）：
 * - 类型 CarParamsAPI 改为对齐后端 Pydantic (L/W/H/wheelbase/...)
 * - 接 GLTFLoader 真实加载 GLB mesh
 * - OrbitControls + 视角预设
 * - 4 统计卡 + 部件详情表
 */
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import * as THREE from 'three'
import { buildCar, getCarPresets } from '@/api/car'
import type { CarParamsAPI, CarBuildResponse } from '@/types/api'

const { t } = useI18n()

// ==================== 参数 ====================

// 22 维默认参数（严格对齐 backend/models/car.py CarParamsAPI）
const defaultParams = (): CarParamsAPI => ({
  L: 4.7, W: 1.85, H: 1.45, wheelbase: 2.8,
  hood_length: 1.1, cabin_length: 2.2, trunk_length: 1.0, ground_clearance: 0.18,
  hood_angle: 12.0, roof_arc: 0.35, windshield_rake: 30.0, rear_glass_angle: 35.0,
  fender_prominence: 0.15, waist_line: 0.8, shoulder_line: 1.0, overall_arc: 0.2,
  glass_darkness: 0.4, wheel_radius: 0.34, wheel_width: 0.22, wheel_spoke_count: 5,
  headlight_width: 0.42, headlight_height: 0.10,
})
const params = reactive<CarParamsAPI>(defaultParams())

// ==================== 状态 ====================

const generating = ref(false)
const lastResult = ref<CarBuildResponse | null>(null)
const lastError = ref<string>('')
const buildProgress = ref(0)
const presets = ref<Record<string, CarParamsAPI>>({})
const autoRotateEnabled = ref(true)

// ==================== Three.js 状态（模块级，不响应式）====================

const canvasRef = ref<HTMLCanvasElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: any = null  // OrbitControls 实例（动态导入，类型用 any）
let currentModel: THREE.Group | null = null
let animationId: number | null = null
let resizeObserver: ResizeObserver | null = null

// ==================== 视角预设 ====================

const viewPresets = [
  { name: '正视图', pos: [0, 1, 8] as [number, number, number], target: [0, 0.7, 0] as [number, number, number] },
  { name: '侧视图', pos: [8, 1, 0] as [number, number, number], target: [0, 0.7, 0] as [number, number, number] },
  { name: '后视图', pos: [0, 1, -8] as [number, number, number], target: [0, 0.7, 0] as [number, number, number] },
  { name: '45°', pos: [5, 3, 5] as [number, number, number], target: [0, 0.7, 0] as [number, number, number] },
  { name: '俯视', pos: [0, 8, 0.01] as [number, number, number], target: [0, 0, 0] as [number, number, number] },
]

function setView(preset: typeof viewPresets[number]) {
  if (!camera || !controls) return
  camera.position.set(...preset.pos)
  controls.target.set(...preset.target)
  controls.update()
  autoRotateEnabled.value = false
  if (controls) controls.autoRotate = false
}

function toggleAutoRotate() {
  if (!controls) return
  autoRotateEnabled.value = !autoRotateEnabled.value
  controls.autoRotate = autoRotateEnabled.value
}

// ==================== Three.js 初始化 ====================

async function initThreeScene() {
  if (!canvasRef.value) return
  const canvas = canvasRef.value
  const width = canvas.clientWidth || 800
  const height = canvas.clientHeight || 500

  // Scene
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0a1929)
  scene.fog = new THREE.Fog(0x0a1929, 15, 35)

  // Camera
  camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100)
  camera.position.set(5, 3, 7)
  camera.lookAt(0, 0.7, 0)

  // Renderer
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(width, height, false)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.0

  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 0.5))
  const dirLight = new THREE.DirectionalLight(0xffffff, 1.0)
  dirLight.position.set(5, 8, 5)
  dirLight.castShadow = true
  dirLight.shadow.mapSize.set(1024, 1024)
  scene.add(dirLight)
  const fillLight = new THREE.PointLight(0x4080ff, 0.4, 20)
  fillLight.position.set(-5, 3, -3)
  scene.add(fillLight)

  // Grid
  const grid = new THREE.GridHelper(20, 20, 0x4a5f7a, 0x2a3f5a)
  grid.position.y = 0
  ;(grid.material as THREE.Material).transparent = true
  ;(grid.material as THREE.Material).opacity = 0.3
  scene.add(grid)

  // Shadow floor
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(20, 20),
    new THREE.ShadowMaterial({ opacity: 0.3 }),
  )
  floor.rotation.x = -Math.PI / 2
  floor.receiveShadow = true
  scene.add(floor)

  // Controls（动态导入，减小主 bundle）
  const { OrbitControls } = await import('three/examples/jsm/controls/OrbitControls.js')
  controls = new OrbitControls(camera, canvas)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 2
  controls.maxDistance = 20
  controls.maxPolarAngle = Math.PI / 2 + 0.1
  controls.target.set(0, 0.7, 0)
  controls.autoRotate = true
  controls.autoRotateSpeed = 0.5
  controls.addEventListener('start', () => {
    autoRotateEnabled.value = false
    controls.autoRotate = false
  })

  // Animation loop
  const animate = () => {
    animationId = requestAnimationFrame(animate)
    if (controls) controls.update()
    if (renderer && scene && camera) renderer.render(scene, camera)
  }
  animate()

  // Resize observer
  resizeObserver = new ResizeObserver(() => {
    if (!canvas || !renderer || !camera) return
    const w = canvas.clientWidth
    const h = canvas.clientHeight
    if (w === 0 || h === 0) return
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h, false)
  })
  resizeObserver.observe(canvas)
}

// ==================== GLB 加载 ====================

async function loadGLB(url: string) {
  if (!scene) return
  const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader.js')
  const loader = new GLTFLoader()

  // 清理旧模型
  if (currentModel) {
    scene.remove(currentModel)
    currentModel.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry?.dispose()
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose())
        else obj.material?.dispose()
      }
    })
    currentModel = null
  }

  // 加载新模型
  try {
    const gltf = await loader.loadAsync(url)
    currentModel = gltf.scene
    currentModel.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.castShadow = true
        obj.receiveShadow = true
      }
    })
    scene.add(currentModel)
  } catch (e) {
    console.error('GLB load failed:', url, e)
    throw new Error(`GLB 加载失败: ${(e as Error).message}`)
  }
}

// ==================== 构建流程 ====================

let debounceTimer: number | null = null
function scheduleGenerate() {
  if (debounceTimer) clearTimeout(debounceTimer)
  buildProgress.value = 0
  debounceTimer = window.setTimeout(() => { void generate() }, 400)
}

async function generate() {
  if (generating.value) return
  generating.value = true
  lastError.value = ''
  try {
    buildProgress.value = 20
    const result = await buildCar(params)
    buildProgress.value = 60
    lastResult.value = result
    buildProgress.value = 80
    await loadGLB(result.glb_url)
    buildProgress.value = 100
    ElMessage.success(`构建完成 · ${result.build_time_ms.toFixed(0)}ms · ${result.stats.total_vertices.toLocaleString()} 顶点`)
  } catch (e: any) {
    lastError.value = e?.response?.data?.detail || e?.message || '未知错误'
    ElMessage.error(`生成失败: ${lastError.value}`)
  } finally {
    generating.value = false
    setTimeout(() => { buildProgress.value = 0 }, 800)
  }
}

function reset() {
  Object.assign(params, defaultParams())
  ElMessage.info('已重置为默认参数')
  scheduleGenerate()
}

async function loadPresets() {
  try {
    const { presets: p } = await getCarPresets()
    presets.value = p
  } catch {
    // 静默失败，UI 上预设按钮会失效
  }
}

function applyPreset(name: string) {
  const p = presets.value[name]
  if (p) {
    Object.assign(params, p)
    ElMessage.success(`已加载预设：${name === 'sport' ? '运动型' : name === 'luxury' ? '豪华型' : 'SUV'}`)
    scheduleGenerate()
  }
}

// 滑块改值时触发重新构建（template @change 调用）
function handleParamChange(): void {
  scheduleGenerate()
}

// 显式 expose（Vue3 自动暴露但 vue-tsc 严格模式偶尔漏掉，强制 expose 最稳）
defineExpose({
  handleParamChange, generate, reset, applyPreset,
  setView, toggleAutoRotate,
})

// ==================== 滑块定义（5 组）====================

const sliderDefs = [
  {
    group: '基础尺寸', icon: 'Crop', sliders: [
      { key: 'L', label: '车长 L', unit: 'm', min: 3.5, max: 5.5, step: 0.05 },
      { key: 'W', label: '车宽 W', unit: 'm', min: 1.6, max: 2.1, step: 0.01 },
      { key: 'H', label: '车高 H', unit: 'm', min: 1.25, max: 1.85, step: 0.01 },
      { key: 'wheelbase', label: '轴距', unit: 'm', min: 2.3, max: 3.2, step: 0.05 },
    ],
  },
  {
    group: '比例姿态', icon: 'DataLine', sliders: [
      { key: 'hood_length', label: '发动机盖长', unit: 'm', min: 0.7, max: 1.5, step: 0.05 },
      { key: 'cabin_length', label: '座舱长', unit: 'm', min: 1.6, max: 2.6, step: 0.05 },
      { key: 'trunk_length', label: '行李箱长', unit: 'm', min: 0.5, max: 1.4, step: 0.05 },
      { key: 'ground_clearance', label: '离地间隙', unit: 'm', min: 0.12, max: 0.25, step: 0.01 },
    ],
  },
  {
    group: '曲面特征', icon: 'MagicStick', sliders: [
      { key: 'hood_angle', label: '机盖角度', unit: '°', min: 5, max: 25, step: 1 },
      { key: 'roof_arc', label: '车顶弧度', unit: '', min: 0, max: 0.8, step: 0.05 },
      { key: 'windshield_rake', label: '前挡风倾角', unit: '°', min: 20, max: 40, step: 1 },
      { key: 'rear_glass_angle', label: '后挡风倾角', unit: '°', min: 25, max: 45, step: 1 },
      { key: 'fender_prominence', label: '轮眉突出', unit: '', min: 0, max: 0.35, step: 0.01 },
      { key: 'waist_line', label: '腰线高度比', unit: '', min: 0.65, max: 0.95, step: 0.01 },
      { key: 'shoulder_line', label: '肩线高度比', unit: '', min: 0.85, max: 1.15, step: 0.01 },
      { key: 'overall_arc', label: '整体弧度', unit: '', min: 0, max: 0.7, step: 0.05 },
    ],
  },
  {
    group: '玻璃与轮', icon: 'Sunny', sliders: [
      { key: 'glass_darkness', label: '玻璃透射', unit: '', min: 0.1, max: 0.7, step: 0.05 },
      { key: 'wheel_radius', label: '轮半径', unit: 'm', min: 0.28, max: 0.40, step: 0.01 },
      { key: 'wheel_width', label: '轮宽', unit: 'm', min: 0.18, max: 0.28, step: 0.01 },
      { key: 'wheel_spoke_count', label: '辐条数', unit: '', min: 3, max: 10, step: 1 },
    ],
  },
  {
    group: '灯', icon: 'Sunrise', sliders: [
      { key: 'headlight_width', label: '大灯宽', unit: 'm', min: 0.30, max: 0.55, step: 0.01 },
      { key: 'headlight_height', label: '大灯高', unit: 'm', min: 0.06, max: 0.16, step: 0.01 },
    ],
  },
] as const

// ==================== 统计 ====================

const statCards = computed(() => {
  const stats = lastResult.value?.stats
  return [
    { label: '顶点数', value: stats?.total_vertices?.toLocaleString() ?? '--', icon: 'Grid' },
    { label: '面数', value: stats?.total_faces?.toLocaleString() ?? '--', icon: 'Cpu' },
    { label: '部件数', value: stats ? Object.keys(stats.components).length : '--', icon: 'Box' },
    { label: '构建耗时', value: lastResult.value ? `${lastResult.value.build_time_ms.toFixed(0)}ms` : '--', icon: 'Timer' },
  ]
})

// ==================== 生命周期 ====================

onMounted(async () => {
  await initThreeScene()
  await loadPresets()
  await generate()  // 首次加载默认参数的 GLB
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (resizeObserver) resizeObserver.disconnect()
  if (controls) controls.dispose()
  if (currentModel && scene) {
    scene.remove(currentModel)
    currentModel.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry?.dispose()
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose())
        else obj.material?.dispose()
      }
    })
  }
  if (renderer) {
    renderer.dispose()
    renderer.forceContextLoss()
  }
})
</script>

<template>
  <div class="designer">
    <el-card class="header-card" shadow="never">
      <div class="header-row">
        <div>
          <h1>{{ t('designer.title') || '造型设计' }}</h1>
          <p class="sub">W2-D1 · 22 维参数 → 后端构建 GLB → Three.js 实时渲染</p>
        </div>
        <div class="header-actions">
          <el-button-group>
            <el-button size="default" :disabled="!presets.sport" @click="applyPreset('sport')">运动型</el-button>
            <el-button size="default" :disabled="!presets.luxury" @click="applyPreset('luxury')">豪华型</el-button>
            <el-button size="default" :disabled="!presets.suv" @click="applyPreset('suv')">SUV</el-button>
          </el-button-group>
          <el-button :loading="generating" type="primary" size="large" @click="generate">
            重新构建
          </el-button>
          <el-button size="large" @click="reset">重置</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- 左：参数面板 -->
      <el-col :xs="24" :md="10" :lg="9">
        <el-card v-for="group in sliderDefs" :key="group.group" shadow="never" class="param-card">
          <template #header>
            <div class="group-header">
              <el-icon><component :is="group.icon" /></el-icon>
              <span>{{ group.group }}</span>
              <el-tag size="small" effect="plain">{{ group.sliders.length }} 维</el-tag>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item v-for="s in group.sliders" :key="s.key" :label="`${s.label} (${s.unit || '-'})`">
              <el-slider
                v-model="(params as any)[s.key]"
                :min="s.min" :max="s.max" :step="s.step"
                show-input :show-input-controls="false"
                @change="handleParamChange"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右：3D 预览 -->
      <el-col :xs="24" :md="14" :lg="15">
        <el-card shadow="never" class="preview-card">
          <template #header>
            <div class="preview-header">
              <span>3D 预览 · 真实 NURBS 曲面</span>
              <div class="preview-tags">
                <el-tag size="small" type="success" effect="plain">Three.js</el-tag>
                <el-tag size="small" type="info" effect="plain">GLTFLoader</el-tag>
                <el-tag size="small" :type="generating ? 'warning' : 'success'" effect="dark">
                  {{ generating ? `构建中 ${buildProgress}%` : '就绪' }}
                </el-tag>
              </div>
            </div>
          </template>

          <div class="canvas-container">
            <canvas ref="canvasRef" class="three-canvas"></canvas>
            <div v-if="generating" class="loading-overlay">
              <el-progress :percentage="buildProgress" :stroke-width="8" :width="160" type="circle" />
              <p>正在重新构建车体...</p>
            </div>
          </div>

          <div class="view-presets">
            <span class="view-label">视角：</span>
            <el-button-group>
              <el-button v-for="vp in viewPresets" :key="vp.name" size="small" @click="setView(vp)">
                {{ vp.name }}
              </el-button>
            </el-button-group>
            <el-button size="small" :type="autoRotateEnabled ? 'primary' : ''" @click="toggleAutoRotate">
              {{ autoRotateEnabled ? '⏸ 停止旋转' : '▶ 自动旋转' }}
            </el-button>
          </div>

          <el-row :gutter="10" class="stats-row">
            <el-col v-for="(stat, i) in statCards" :key="i" :span="6">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-content">
                  <el-icon :size="20" color="#409EFF"><component :is="stat.icon" /></el-icon>
                  <div>
                    <div class="stat-value">{{ stat.value }}</div>
                    <div class="stat-label">{{ stat.label }}</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-alert
            v-if="lastError"
            :title="`构建失败：${lastError}`"
            type="error" :closable="true" show-icon
            @close="lastError = ''"
            class="error-alert"
          />

          <el-collapse v-if="lastResult" class="components-collapse">
            <el-collapse-item :title="`部件详情 (${Object.keys(lastResult.stats.components).length} 个)`" name="1">
              <el-table
                :data="Object.entries(lastResult.stats.components).map(([name, c]) => ({
                  name, vertices: c.vertices, faces: c.faces, color: c.color,
                }))"
                stripe size="small" max-height="200"
              >
                <el-table-column prop="name" label="部件" width="120" />
                <el-table-column prop="vertices" label="顶点数" align="right" />
                <el-table-column prop="faces" label="面数" align="right" />
                <el-table-column label="颜色" width="100">
                  <template #default="{ row }">
                    <div class="color-swatch" :style="{ background: row.color }"></div>
                    <span class="color-text">{{ row.color }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.designer { max-width: 1600px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
.header-row h1 { margin: 0 0 4px; font-size: 22px; }
.header-row .sub { margin: 0; color: #909399; font-size: 13px; }
.header-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }

.param-card { margin-bottom: 16px; }
.group-header { display: flex; align-items: center; gap: 8px; }
.param-card :deep(.el-form-item) { margin-bottom: 14px; }

.preview-card { position: sticky; top: 20px; }
.preview-header { display: flex; justify-content: space-between; align-items: center; }
.preview-tags { display: flex; gap: 6px; }

.canvas-container {
  position: relative;
  width: 100%;
  height: 500px;
  background: #0a1929;
  border-radius: 8px;
  overflow: hidden;
}
.three-canvas { width: 100%; height: 100%; display: block; }
.loading-overlay {
  position: absolute; inset: 0;
  background: rgba(10, 25, 41, 0.85);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 16px;
  color: #fff;
}

.view-presets {
  display: flex; align-items: center; gap: 12px;
  margin: 16px 0;
  flex-wrap: wrap;
}
.view-label { font-size: 14px; color: #606266; }

.stats-row { margin: 16px 0; }
.stat-card { cursor: default; }
.stat-content { display: flex; align-items: center; gap: 10px; }
.stat-value { font-size: 18px; font-weight: 600; color: #303133; }
.stat-label { font-size: 12px; color: #909399; }

.error-alert { margin-top: 12px; }
.components-collapse { margin-top: 12px; }
.color-swatch { display: inline-block; width: 20px; height: 20px; border-radius: 4px; border: 1px solid #dcdfe6; vertical-align: middle; margin-right: 8px; }
.color-text { font-family: monospace; font-size: 12px; color: #909399; }
</style>
