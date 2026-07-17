<script setup lang="ts">
/**
 * 分镜项目详情（W1-D3）
 * 单个分镜项目的 6 镜头展示 + 渲染输出
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.projectId as string)

const demoScenes = [
  { title: '开场 · 品牌片头', desc: '航拍清晨城市天际线，光影掠过玻璃幕墙', camera: '航拍', duration: '15s' },
  { title: '问题引入', desc: '传统汽车造型开发周期长、成本高、迭代慢', camera: '中景', duration: '15s' },
  { title: '产品介绍', desc: 'EVOLUTION AI 22 维参数化建模，实时 3D 预览', camera: '特写', duration: '20s' },
  { title: '核心能力', desc: 'AI 优化 + 质量评估 + 反射线分析，端到端 5s', camera: '环绕', duration: '20s' },
  { title: '技术亮点', desc: 'WebSocket 实时进度 · Three.js 场景 · G2/A 级曲面', camera: '推拉', duration: '15s' },
  { title: '结尾 CTA', desc: 'EVOLUTION AI · 让设计更快、更准、更美', camera: '全景', duration: '5s' },
]
</script>

<template>
  <div class="storyboard-detail">
    <el-card class="header-card" shadow="never">
      <div class="header-row">
        <div>
          <h1>{{ t('storyboardDetail.title') }}</h1>
          <p class="sub">project_id: <code>{{ projectId }}</code></p>
        </div>
        <el-button @click="router.push('/storyboard')">返回列表</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="scenes-header">
          <span>{{ t('storyboardDetail.scenes') }} (6 镜头)</span>
          <div>
            <el-button size="small">{{ t('storyboardDetail.render') }}</el-button>
            <el-button size="small" type="primary">{{ t('storyboardDetail.export') }}</el-button>
          </div>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col v-for="(scene, idx) in demoScenes" :key="idx" :xs="24" :sm="12" :md="8">
          <el-card class="scene-card" shadow="hover">
            <div class="scene-num">{{ idx + 1 }}</div>
            <h3>{{ scene.title }}</h3>
            <p class="scene-desc">{{ scene.desc }}</p>
            <div class="scene-meta">
              <el-tag size="small" effect="plain">{{ scene.camera }}</el-tag>
              <el-tag size="small" type="info" effect="plain">{{ scene.duration }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.storyboard-detail { max-width: 1280px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
.header-row h1 { margin: 0 0 4px; font-size: 22px; }
.header-row .sub { margin: 0; color: #909399; font-size: 13px; }
.header-row code { background: #f4f4f5; padding: 2px 8px; border-radius: 3px; font-family: monospace; }
.scenes-header { display: flex; justify-content: space-between; align-items: center; }
.scene-card { margin-bottom: 16px; position: relative; }
.scene-num {
  position: absolute; top: 12px; right: 12px;
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #4f46e5, #06b6d4); color: #fff;
  display: inline-flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700;
}
.scene-card h3 { margin: 0 0 8px; font-size: 15px; padding-right: 40px; }
.scene-desc { color: #606266; font-size: 13px; line-height: 1.6; margin: 0 0 8px; }
.scene-meta { display: flex; gap: 6px; }
</style>
