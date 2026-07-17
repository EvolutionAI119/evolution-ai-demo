<script setup lang="ts">
/**
 * 500 错误页（W1-D3）
 */
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()
const countdown = ref<number>(5)

let timer: number | null = null

function reloadPage(): void {
  window.location.reload()
}

onMounted(() => {
  timer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      router.push('/')
    }
  }, 1000)
})
</script>

<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-icon">🔥</div>
      <h1>{{ t('errors.serverError.title') }}</h1>
      <p>{{ t('errors.serverError.desc') }}</p>
      <p class="countdown">{{ countdown }} 秒后自动回首页</p>
      <el-button type="primary" size="large" @click="router.push('/')" style="margin-right: 8px;">
        {{ t('errors.serverError.back') }}
      </el-button>
      <el-button size="large" @click="reloadPage">
        {{ t('errors.serverError.retry') }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  min-height: calc(100vh - 60px);
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #fef3c7 0%, #fecaca 100%);
}
.error-content { text-align: center; max-width: 480px; padding: 40px; }
.error-icon { font-size: 96px; margin-bottom: 24px; }
.error-content h1 { font-size: 28px; color: #303133; margin: 0 0 12px; }
.error-content p { color: #606266; font-size: 14px; line-height: 1.6; margin: 0 0 8px; }
.countdown { color: #909399; font-size: 12px; margin-bottom: 24px !important; }
</style>
