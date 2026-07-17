<script setup lang="ts">
/**
 * 质量评估页面（W1-D3）
 * 4 个预设曲面 + G0/G1/G2 指标卡片 + 反射线评分
 */
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import api from '@/api'

const { t } = useI18n()

const shape = ref<string>('sphere')
const resolution = ref<number>(20)
const assessing = ref(false)
const report = ref<{
  panel_name: string; grade: string;
  g0_count: number; g1_count: number; g2_count: number;
  g1_ratio: number; g2_ratio: number;
  max_curvature_jump: number; mean_curvature: number;
  reflection_score: number;
} | null>(null)

async function assess() {
  assessing.value = true
  try {
    const { data } = await api.post('/api/v1/quality/assess-preset', {
      shape: shape.value,
      resolution: resolution.value,
    })
    report.value = data
    ElMessage.success(`评估完成：${data.grade}级曲面`)
  } catch (e) {
    ElMessage.error(`评估失败: ${(e as Error).message}`)
  } finally {
    assessing.value = false
  }
}

const gradeColor = (g: string) => ({
  A: 'success', B: 'primary', C: 'warning', D: 'danger',
}[g] || 'info')
</script>

<template>
  <div class="quality">
    <el-card class="header-card" shadow="never">
      <h1>{{ t('quality.title') }}</h1>
      <p class="sub">{{ t('quality.subtitle') }}</p>
    </el-card>

    <el-row :gutter="20">
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <template #header><span>评估配置</span></template>
          <el-form label-position="top">
            <el-form-item :label="t('optimize.params.shape')">
              <el-select v-model="shape" style="width: 100%;">
                <el-option :label="t('optimize.shape.sphere')" value="sphere" />
                <el-option :label="t('optimize.shape.plane')" value="plane" />
                <el-option :label="t('optimize.shape.cylinder')" value="cylinder" />
                <el-option :label="t('optimize.shape.carBody')" value="car_body" />
              </el-select>
            </el-form-item>
            <el-form-item label="分辨率 (n)">
              <el-input-number v-model="resolution" :min="10" :max="40" :step="2" style="width: 100%;" />
            </el-form-item>
            <el-button :loading="assessing" type="primary" size="large" style="width: 100%;" @click="assess">
              {{ t('quality.actions.assess') }}
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16">
        <el-card v-if="report" shadow="never">
          <template #header>
            <div class="report-header">
              <span>{{ report.panel_name }} · 评估报告</span>
              <el-tag :type="gradeColor(report.grade) as any" effect="dark" size="large">
                {{ t(`quality.grade.${report.grade}`) }}
              </el-tag>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-statistic :title="t('quality.metrics.g0Count')" :value="report.g0_count" />
            </el-col>
            <el-col :span="8">
              <el-statistic :title="t('quality.metrics.g1Count')" :value="report.g1_count" :value-style="{ color: '#409eff' }" />
            </el-col>
            <el-col :span="8">
              <el-statistic :title="t('quality.metrics.g2Count')" :value="report.g2_count" :value-style="{ color: '#67c23a' }" />
            </el-col>
            <el-col :span="8" style="margin-top: 16px;">
              <el-statistic :title="t('quality.metrics.g2Ratio')" :value="report.g2_ratio" :precision="3" :value-style="{ color: '#67c23a' }" />
            </el-col>
            <el-col :span="8" style="margin-top: 16px;">
              <el-statistic :title="t('quality.metrics.reflection')" :value="report.reflection_score" :precision="3" :value-style="{ color: '#e6a23c' }" />
            </el-col>
            <el-col :span="8" style="margin-top: 16px;">
              <el-statistic :title="t('quality.metrics.meanCurvature')" :value="report.mean_curvature" :precision="3" />
            </el-col>
            <el-col :span="24" style="margin-top: 16px;">
              <el-statistic :title="t('quality.metrics.maxJump')" :value="report.max_curvature_jump" :precision="2" suffix="°" />
            </el-col>
          </el-row>
        </el-card>
        <el-card v-else shadow="never">
          <el-empty description="点击左侧「开始评估」生成报告" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.quality { max-width: 1280px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-card h1 { margin: 0 0 4px; font-size: 22px; }
.header-card .sub { margin: 0; color: #909399; font-size: 13px; }
.report-header { display: flex; justify-content: space-between; align-items: center; }
</style>
