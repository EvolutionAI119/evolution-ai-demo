<script setup lang="ts">
/**
 * 造型设计页面（W1-D3）
 * 11 个核心参数滑块 + 实时预览占位 + 保存方案
 * 实际 3D 预览由 W2-D1 接入 Three.js 完成
 */
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

const { t } = useI18n()

// 11 个核心参数（默认值参照 CarParams 默认）
const params = reactive({
  bodyLength: 4.7,
  bodyWidth: 1.85,
  bodyHeight: 1.45,
  wheelbase: 2.75,
  frontOverhang: 0.95,
  rearOverhang: 1.0,
  groundClearance: 0.18,
  roofHeight: 1.4,
  windshieldAngle: 28,
  rearWindowAngle: 32,
  hoodAngle: 12,
})

const generating = ref(false)
const lastResult = ref<string>('')

async function generate() {
  generating.value = true
  try {
    const { data } = await import('@/api').then((m) => m.default.post('/api/v1/car/build', {
      L: params.bodyLength,
      W: params.bodyWidth,
      H: params.bodyHeight,
      wheelbase: params.wheelbase,
      front_overhang: params.frontOverhang,
      rear_overhang: params.rearOverhang,
      ground_clearance: params.groundClearance,
      roof_height: params.roofHeight,
      windshield_angle: params.windshieldAngle,
      rear_window_angle: params.rearWindowAngle,
      hood_angle: params.hoodAngle,
    }))
    lastResult.value = `parts: ${Object.keys(data).join(', ')}`
    ElMessage.success(t('designer.status.done'))
  } catch (e) {
    ElMessage.error(`生成失败: ${(e as Error).message}`)
  } finally {
    generating.value = false
  }
}

function reset() {
  Object.assign(params, {
    bodyLength: 4.7,
    bodyWidth: 1.85,
    bodyHeight: 1.45,
    wheelbase: 2.75,
    frontOverhang: 0.95,
    rearOverhang: 1.0,
    groundClearance: 0.18,
    roofHeight: 1.4,
    windshieldAngle: 28,
    rearWindowAngle: 32,
    hoodAngle: 12,
  })
}
</script>

<template>
  <div class="designer">
    <el-card class="header-card" shadow="never">
      <div class="header-row">
        <div>
          <h1>{{ t('designer.title') }}</h1>
          <p class="sub">{{ t('designer.subtitle') }}</p>
        </div>
        <div class="header-actions">
          <el-button :loading="generating" type="primary" size="large" @click="generate">
            {{ t('designer.actions.generate') }}
          </el-button>
          <el-button size="large" @click="reset">
            {{ t('designer.actions.reset') }}
          </el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span>核心参数（11 维）</span></template>
          <el-form label-position="top">
            <el-form-item :label="t('designer.params.bodyLength')">
              <el-slider v-model="params.bodyLength" :min="3.5" :max="5.5" :step="0.05" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.bodyWidth')">
              <el-slider v-model="params.bodyWidth" :min="1.6" :max="2.1" :step="0.01" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.bodyHeight')">
              <el-slider v-model="params.bodyHeight" :min="1.2" :max="1.7" :step="0.01" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.wheelbase')">
              <el-slider v-model="params.wheelbase" :min="2.3" :max="3.2" :step="0.05" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.frontOverhang')">
              <el-slider v-model="params.frontOverhang" :min="0.7" :max="1.2" :step="0.01" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.rearOverhang')">
              <el-slider v-model="params.rearOverhang" :min="0.7" :max="1.3" :step="0.01" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.groundClearance')">
              <el-slider v-model="params.groundClearance" :min="0.1" :max="0.25" :step="0.01" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.roofHeight')">
              <el-slider v-model="params.roofHeight" :min="1.2" :max="1.55" :step="0.01" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.windshieldAngle')">
              <el-slider v-model="params.windshieldAngle" :min="20" :max="40" :step="1" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.rearWindowAngle')">
              <el-slider v-model="params.rearWindowAngle" :min="25" :max="45" :step="1" show-input :show-input-controls="false" />
            </el-form-item>
            <el-form-item :label="t('designer.params.hoodAngle')">
              <el-slider v-model="params.hoodAngle" :min="5" :max="20" :step="1" show-input :show-input-controls="false" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="preview-card">
          <template #header>
            <div class="preview-header">
              <span>3D 预览</span>
              <el-tag size="small" type="info" effect="plain">W2-D1 接入</el-tag>
            </div>
          </template>
          <div class="preview-placeholder">
            <el-icon :size="64" color="#c0c4cc"><Box /></el-icon>
            <p>Three.js 场景占位</p>
            <p class="hint">W2-D1 启动后挂载</p>
          </div>
          <el-alert v-if="lastResult" :title="lastResult" type="success" :closable="false" show-icon />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.designer { max-width: 1280px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
.header-row h1 { margin: 0 0 4px; font-size: 22px; }
.header-row .sub { margin: 0; color: #909399; font-size: 13px; }
.header-actions { display: flex; gap: 8px; }
.preview-card .preview-header { display: flex; justify-content: space-between; align-items: center; }
.preview-placeholder {
  height: 400px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: #f5f7fa; border-radius: 8px; gap: 8px; color: #909399;
}
.preview-placeholder p { margin: 0; font-size: 14px; }
.preview-placeholder .hint { font-size: 12px; color: #c0c4cc; }
</style>
