<script setup lang="ts">
/**
 * 首页 - M3 状态仪表盘（W1-D2：i18n 化）
 *
 * 显示：5 大业务模块 + 后端连通性 + 当前版本
 */
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const { t } = useI18n()

const backendStatus = ref<'unknown' | 'online' | 'offline'>('unknown')
const openapiVersion = ref<string>('--')
const endpointCount = ref<number>(0)

// M3 当前进度的 W1-D{n}（从 i18n 里取，外部数据源后续接 build-info）
const m3Day = ref<number>(2)

onMounted(async () => {
  try {
    // 后端 /health 不在 /api/v1 前缀下，用绝对路径跳过 baseURL
    const health = await axios.get('/health', { timeout: 3000 })
    backendStatus.value = health.status === 200 ? 'online' : 'offline'
    const spec = await axios.get('/api/v1/openapi.json', { timeout: 3000 })
    openapiVersion.value = spec.data?.info?.version ?? '--'
    endpointCount.value = Object.keys(spec.data?.paths ?? {}).length
  } catch {
    backendStatus.value = 'offline'
  }
})

// 5 大模块（用 i18n key 而非硬编码）
const moduleKeys = [
  { path: '/designer', labelKey: 'home.modules.designer.label', descKey: 'home.modules.designer.desc', icon: 'Brush', tag: 'W1-D3' },
  { path: '/quality', labelKey: 'home.modules.quality.label', descKey: 'home.modules.quality.desc', icon: 'DataAnalysis', tag: 'W1-D3' },
  { path: '/optimize', labelKey: 'home.modules.optimize.label', descKey: 'home.modules.optimize.desc', icon: 'MagicStick', tag: 'W1-D3' },
  { path: '/storyboard', labelKey: 'home.modules.storyboard.label', descKey: 'home.modules.storyboard.desc', icon: 'VideoCamera', tag: 'W1-D3' },
  { path: '/projects', labelKey: 'home.modules.projects.label', descKey: 'home.modules.projects.desc', icon: 'Folder', tag: 'W1-D3' },
] as const

const backendTagType = computed(() => (backendStatus.value === 'online' ? 'success' : 'danger'))
const backendTagText = computed(() => {
  if (backendStatus.value === 'online') return t('home.status.backendOnline')
  if (backendStatus.value === 'offline') return t('home.status.backendOffline')
  return t('home.status.backendUnknown')
})

const apiTagText = computed(() =>
  t('home.status.apiEndpoints', { version: openapiVersion.value, count: endpointCount.value })
)
const skeletonTagText = computed(() => t('home.status.m3Skeleton', { day: m3Day.value }))
const sectionTitleText = computed(() => t('home.sectionTitle', { count: moduleKeys.length }))
</script>

<template>
  <div class="home">
    <el-card class="hero" shadow="never">
      <div class="hero-content">
        <div>
          <h1>{{ t('home.hero.title') }}</h1>
          <p>{{ t('home.hero.subtitle') }}</p>
          <div class="status">
            <el-tag :type="backendTagType" effect="dark">
              <el-icon><Connection /></el-icon>
              {{ backendTagText }}
            </el-tag>
            <el-tag type="info" effect="plain">{{ apiTagText }}</el-tag>
            <el-tag type="warning" effect="plain">{{ skeletonTagText }}</el-tag>
          </div>
        </div>
        <el-icon class="hero-icon" :size="80"><Lightning /></el-icon>
      </div>
    </el-card>

    <h2 class="section-title">{{ sectionTitleText }}</h2>
    <el-row :gutter="20">
      <el-col v-for="m in moduleKeys" :key="m.path" :xs="24" :sm="12" :md="8" :lg="8" :xl="8">
        <el-card class="module-card" shadow="hover" @click="$router.push(m.path)">
          <div class="module-icon">
            <el-icon :size="32"><component :is="m.icon" /></el-icon>
          </div>
          <div class="module-body">
            <div class="module-title">
              <span>{{ t(m.labelKey) }}</span>
              <el-tag size="small" effect="plain">{{ m.tag }}</el-tag>
            </div>
            <div class="module-desc">{{ t(m.descKey) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.home {
  max-width: 1280px;
  margin: 0 auto;
}

.hero {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: #fff;
  margin-bottom: 28px;
  border: none;
}

.hero :deep(.el-card__body) {
  padding: 32px;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hero h1 {
  margin: 0 0 8px;
  font-size: 32px;
  background: linear-gradient(90deg, #fff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero p {
  margin: 0 0 16px;
  color: #c0d3f0;
  font-size: 14px;
}

.status {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hero-icon {
  color: rgba(255, 255, 255, 0.3);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 24px 0 16px;
  color: #303133;
}

.module-card {
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 16px;
}

.module-card:hover {
  transform: translateY(-2px);
}

.module-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  padding: 20px;
}

.module-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-right: 16px;
  flex-shrink: 0;
}

.module-body {
  flex: 1;
  min-width: 0;
}

.module-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.module-desc {
  font-size: 12px;
  color: #909399;
}
</style>
