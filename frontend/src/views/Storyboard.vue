<script setup lang="ts">
/**
 * 分镜脚本列表（W1-D3）
 * 4 模板选择 + 产品参数 + 渲染
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import api from '@/api'

const { t } = useI18n()

const productName = ref<string>('EVOLUTION AI')
const duration = ref<number>(90)
const style = ref<string>('高端汽车广告 / 科技感蓝紫色调')
const template = ref<string>('car_promotion')
const generating = ref(false)
const storyboard = ref<any>(null)
const renderedMd = ref<string>('')

async function generate() {
  generating.value = true
  try {
    const { data } = await api.post('/api/v1/storyboard/generate', {
      product_name: productName.value,
      duration: duration.value,
      style: style.value,
      template: template.value,
    })
    storyboard.value = data
    const { data: md } = await api.post('/api/v1/storyboard/render', {
      storyboard: data,
      fmt: 'markdown',
    })
    renderedMd.value = md
    ElMessage.success('分镜已生成')
  } catch (e) {
    ElMessage.error(`生成失败: ${(e as Error).message}`)
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div class="storyboard">
    <el-card class="header-card" shadow="never">
      <h1>{{ t('storyboard.title') }}</h1>
      <p class="sub">{{ t('storyboard.subtitle') }}</p>
    </el-card>

    <el-row :gutter="20">
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <template #header><span>分镜配置</span></template>
          <el-form label-position="top">
            <el-form-item :label="t('storyboard.params.productName')">
              <el-input v-model="productName" />
            </el-form-item>
            <el-form-item :label="t('storyboard.params.duration')">
              <el-input-number v-model="duration" :min="30" :max="300" :step="10" style="width: 100%;" />
            </el-form-item>
            <el-form-item :label="t('storyboard.params.style')">
              <el-input v-model="style" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item :label="t('storyboard.params.template')">
              <el-select v-model="template" style="width: 100%;">
                <el-option :label="t('storyboard.templates.carPromotion')" value="car_promotion" />
                <el-option :label="t('storyboard.templates.techDemo')" value="tech_demo" />
                <el-option :label="t('storyboard.templates.minimalShowcase')" value="minimal_showcase" />
              </el-select>
            </el-form-item>
            <el-button :loading="generating" type="primary" size="large" style="width: 100%;" @click="generate">
              {{ t('storyboard.actions.generate') }}
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16">
        <el-card v-if="storyboard" shadow="never">
          <template #header>
            <div class="scenes-header">
              <span>{{ t('storyboard.scenes.title') }} ({{ storyboard.scenes?.length ?? 0 }} 镜头)</span>
              <el-tag size="small" effect="plain">{{ storyboard.template }}</el-tag>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col v-for="(scene, idx) in storyboard.scenes" :key="idx" :xs="24" :sm="12">
              <el-card class="scene-card" shadow="hover">
                <div class="scene-header">
                  <span class="scene-num">{{ idx + 1 }}</span>
                  <span class="scene-title">{{ scene.title || scene.shot_type || `镜头 ${idx + 1}` }}</span>
                </div>
                <p class="scene-desc">{{ scene.description || scene.content || scene.visual }}</p>
                <div class="scene-meta">
                  <el-tag size="small" effect="plain">{{ scene.duration || '10s' }}</el-tag>
                  <el-tag v-if="scene.camera" size="small" type="info" effect="plain">{{ scene.camera }}</el-tag>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-card>
        <el-card v-else shadow="never">
          <el-empty description="点击「生成分镜」生成 6 镜头脚本" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.storyboard { max-width: 1280px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-card h1 { margin: 0 0 4px; font-size: 22px; }
.header-card .sub { margin: 0; color: #909399; font-size: 13px; }
.scenes-header { display: flex; justify-content: space-between; align-items: center; }
.scene-card { margin-bottom: 16px; }
.scene-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.scene-num {
  width: 24px; height: 24px; border-radius: 50%;
  background: linear-gradient(135deg, #4f46e5, #06b6d4); color: #fff;
  display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;
}
.scene-title { font-weight: 600; font-size: 14px; }
.scene-desc { color: #606266; font-size: 13px; line-height: 1.6; margin: 0 0 8px; }
.scene-meta { display: flex; gap: 6px; }
</style>
