<script setup lang="ts">
/**
 * 项目详情（W1-D3）
 * 5 tab：概览 / 3D / 优化历史 / 质量评估 / 分镜脚本
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.projectId as string)

const activeTab = ref<string>('overview')
const project = ref<any>(null)

async function fetchProject() {
  try {
    const { data } = await api.get(`/api/v1/project/${projectId.value}`)
    project.value = data
  } catch {
    project.value = { id: projectId.value, name: `方案 #${projectId.value}` }
  }
}

onMounted(fetchProject)
</script>

<template>
  <div class="project-detail">
    <el-card class="header-card" shadow="never">
      <div class="header-row">
        <div>
          <h1>{{ t('projectDetail.title') }}</h1>
          <p class="sub">project_id: <code>{{ projectId }}</code> · {{ project?.name ?? '加载中…' }}</p>
        </div>
        <el-button @click="router.push('/projects')">{{ t('projectDetail.actions.back') }}</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="t('projectDetail.tabs.overview')" name="overview">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目 ID">{{ projectId }}</el-descriptions-item>
            <el-descriptions-item label="项目名称">{{ project?.name ?? '--' }}</el-descriptions-item>
            <el-descriptions-item label="曲面类型">{{ project?.surface_type ?? '--' }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ project?.status ?? '--' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间" :span="2">{{ project?.created_at ?? '--' }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
        <el-tab-pane :label="t('projectDetail.tabs.model3d')" name="model3d">
          <el-empty description="W2-D1 接入 Three.js 场景后显示" />
        </el-tab-pane>
        <el-tab-pane :label="t('projectDetail.tabs.optimize')" name="optimize">
          <el-empty description="该项目暂无优化历史" />
        </el-tab-pane>
        <el-tab-pane :label="t('projectDetail.tabs.quality')" name="quality">
          <el-empty description="该项目暂无质量评估" />
        </el-tab-pane>
        <el-tab-pane :label="t('projectDetail.tabs.storyboard')" name="storyboard">
          <el-empty description="该项目暂无分镜脚本" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.project-detail { max-width: 1280px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
.header-row h1 { margin: 0 0 4px; font-size: 22px; }
.header-row .sub { margin: 0; color: #909399; font-size: 13px; }
.header-row code { background: #f4f4f5; padding: 2px 8px; border-radius: 3px; font-family: monospace; }
</style>
