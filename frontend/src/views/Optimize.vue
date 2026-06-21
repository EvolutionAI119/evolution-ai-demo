<script setup lang="ts">
/**
 * AI 优化页面（W1-D3）
 * 4 shape 选择 + max_iter 配置 + 异步任务提交 + 跳详情看 WS 进度
 * WS 实时进度由 W1-D4 在 OptimizeDetail.vue 接入
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const { t } = useI18n()
const router = useRouter()

const shape = ref<string>('sphere')
const maxIter = ref<number>(50)
const panelName = ref<string>('panel')
const seed = ref<number>(42)
const submitting = ref(false)

async function startAsync() {
  submitting.value = true
  try {
    const { data } = await api.post('/api/v1/optimize/start-preset', {
      shape: shape.value,
      max_iter: maxIter.value,
    })
    ElMessage.success(`任务已创建：${data.task_id}`)
    router.push(`/optimize/${data.task_id}`)
  } catch (e) {
    ElMessage.error(`提交失败: ${(e as Error).message}`)
  } finally {
    submitting.value = false
  }
}

async function runSync() {
  submitting.value = true
  try {
    const { data } = await api.post('/api/v1/optimize/run-preset', {
      shape: shape.value,
      max_iter: maxIter.value,
    })
    ElMessage.success(`同步完成：${data.initial_grade} → ${data.final_grade}`)
  } catch (e) {
    ElMessage.error(`同步失败: ${(e as Error).message}`)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="optimize">
    <el-card class="header-card" shadow="never">
      <h1>{{ t('optimize.title') }}</h1>
      <p class="sub">{{ t('optimize.subtitle') }}</p>
    </el-card>

    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span>优化配置</span></template>
          <el-form label-position="top">
            <el-form-item :label="t('optimize.params.shape')">
              <el-radio-group v-model="shape">
                <el-radio-button value="sphere">{{ t('optimize.shape.sphere') }}</el-radio-button>
                <el-radio-button value="plane_with_noise">{{ t('optimize.shape.plane') }}</el-radio-button>
                <el-radio-button value="cylinder">{{ t('optimize.shape.cylinder') }}</el-radio-button>
                <el-radio-button value="car_body">{{ t('optimize.shape.carBody') }}</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item :label="t('optimize.params.maxIter')">
              <el-input-number v-model="maxIter" :min="10" :max="500" :step="10" style="width: 100%;" />
            </el-form-item>
            <el-form-item :label="t('optimize.params.panelName')">
              <el-input v-model="panelName" />
            </el-form-item>
            <el-form-item :label="t('optimize.params.seed')">
              <el-input-number v-model="seed" :min="0" :max="9999" style="width: 100%;" />
            </el-form-item>
            <el-button :loading="submitting" type="primary" size="large" style="width: 100%; margin-bottom: 8px;" @click="startAsync">
              {{ t('optimize.actions.start') }}
            </el-button>
            <el-button :loading="submitting" size="large" style="width: 100%;" @click="runSync">
              {{ t('optimize.actions.startSync') }}
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="info-card">
          <template #header><span>4 预设曲面演示</span></template>
          <ul class="info-list">
            <li><strong>球面</strong>：20×20 meshgrid，模拟退火快速收敛至 A 级</li>
            <li><strong>带噪平面</strong>：高斯噪声演示优化效果最显著</li>
            <li><strong>圆柱</strong>：几何对称曲面，验证 G2 比率</li>
            <li><strong>车身侧围</strong>：49×48 真实车身数据（W1-D2.5 修复后可用）</li>
          </ul>
          <el-divider />
          <p class="footnote">异步任务会跳转到 <code>/optimize/:taskId</code> 详情页，WS 实时进度由 W1-D4 接入</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.optimize { max-width: 1280px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-card h1 { margin: 0 0 4px; font-size: 22px; }
.header-card .sub { margin: 0; color: #909399; font-size: 13px; }
.info-list { padding-left: 20px; color: #606266; line-height: 1.8; }
.info-list li { margin-bottom: 4px; }
.footnote { color: #909399; font-size: 12px; }
.footnote code { background: #f4f4f5; padding: 1px 6px; border-radius: 3px; font-size: 12px; }
</style>
