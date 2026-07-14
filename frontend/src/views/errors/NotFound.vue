<script setup lang="ts">
/**
 * 404 错误页（W1-D3）
 */
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()
</script>

<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-icon">🚧</div>
      <h1>{{ t('errors.notFound.title') }}</h1>
      <p>{{ t('errors.notFound.desc') }}</p>
      <el-button type="primary" size="large" @click="router.push('/')">
        {{ t('errors.notFound.back') }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  min-height: calc(100vh - 60px);
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e0e7ff 100%);
}
.error-content { text-align: center; max-width: 480px; padding: 40px; }
.error-icon { font-size: 96px; margin-bottom: 24px; }
.error-content h1 { font-size: 28px; color: #303133; margin: 0 0 12px; }
.error-content p { color: #606266; font-size: 14px; line-height: 1.6; margin: 0 0 32px; }
</style>
