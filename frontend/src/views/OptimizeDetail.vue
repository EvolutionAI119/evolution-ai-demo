<script setup lang="ts">
/**
 * 优化任务详情（W1-D4: WebSocket 实时进度）
 * - 用 OptimizeWS 订阅 /api/v1/ws/optimize/{task_id}
 * - 4 消息分发：STARTED / PROGRESS / SUCCESS / FAILURE
 * - 断线重连由 ws.ts 内部处理（指数退避，最多 8 次）
 */
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { OptimizeWS, type WSProgressMessage, type WSConnState } from '@/utils/ws'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.taskId as string)

// 任务状态（由 WS 消息填充）
const status = ref<string>('PENDING')
const progress = ref<number>(0)
const currentIter = ref<number>(0)
const maxIter = ref<number>(0)
const result = ref<any>(null)
const errorMsg = ref<string>('')
const panelName = ref<string>('')
const surfaceType = ref<string>('')

// WS 连接状态
const connState = ref<WSConnState>('connecting')
let ws: OptimizeWS | null = null
let unsubscribeMsg: (() => void) | null = null
let unsubscribeState: (() => void) | null = null

function handleMessage(msg: WSProgressMessage) {
  status.value = msg.type
  if (typeof msg.progress === 'number') progress.value = msg.progress
  if (typeof msg.current_iter === 'number') currentIter.value = msg.current_iter
  if (typeof msg.max_iter === 'number' && msg.max_iter > 0) maxIter.value = msg.max_iter
  if (msg.result) result.value = msg.result
  if (msg.error) errorMsg.value = msg.error
  console.info(`[OptimizeDetail] WS msg: ${msg.type} ${msg.current_iter ?? '-'}/${msg.max_iter ?? '-'} ${(msg.progress ?? 0 * 100).toFixed(1)}%`)
}

function handleState(s: WSConnState) {
  connState.value = s
}

onMounted(() => {
  if (!taskId.value) return
  ws = new OptimizeWS(taskId.value, { maxReconnect: 8, maxBackoffMs: 30000 })
  unsubscribeMsg = ws.onMessage(handleMessage)
  unsubscribeState = ws.onStateChange(handleState)
  ws.connect()
})

onUnmounted(() => {
  unsubscribeMsg?.()
  unsubscribeState?.()
  ws?.close()
  ws = null
})

const statusColor = computed(() => ({
  PENDING: 'info', STARTED: 'warning', PROGRESS: 'warning', SUCCESS: 'success', FAILURE: 'danger',
}[status.value] || 'info'))

const connStateColor = computed(() => ({
  connecting: '#909399', open: '#67c23a', reconnecting: '#e6a23c', closed: '#909399', failed: '#f56c6c',
}[connState.value] || '#909399'))

const connStateText = computed(() => ({
  connecting: '连接中', open: '● 实时', reconnecting: '↻ 重连中', closed: '已断开', failed: '连接失败',
}[connState.value] || connState.value))
</script>

<template>
  <div class="optimize-detail">
    <el-card class="header-card" shadow="never">
      <div class="header-row">
        <div>
          <h1>{{ t('optimizeDetail.title') }}</h1>
          <p class="sub">
            task_id: <code>{{ taskId }}</code>
            <span class="conn-state" :style="{ color: connStateColor }">  {{ connStateText }}</span>
          </p>
        </div>
        <el-button @click="router.push('/optimize')">返回列表</el-button>
      </div>
    </el-card>

    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span>{{ t('optimizeDetail.taskInfo') }}</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="状态">
              <el-tag :type="statusColor as any" effect="dark">{{ status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="panelName" label="面板名称">{{ panelName }}</el-descriptions-item>
            <el-descriptions-item v-if="surfaceType" label="曲面类型">{{ surfaceType }}</el-descriptions-item>
            <el-descriptions-item label="最大迭代">{{ maxIter || '—' }}</el-descriptions-item>
            <el-descriptions-item label="当前迭代">{{ currentIter }}</el-descriptions-item>
            <el-descriptions-item label="进度">
              <el-progress
                :percentage="Math.round(progress * 100)"
                :status="status === 'FAILURE' ? 'exception' : status === 'SUCCESS' ? 'success' : ''" />
            </el-descriptions-item>
            <el-descriptions-item v-if="errorMsg" label="错误信息">
              <span style="color: #f56c6c;">{{ errorMsg }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span>{{ t('optimizeDetail.result') }}</span></template>
          <div v-if="result">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-statistic :title="t('optimizeDetail.initial') + ' 等级'" :value="result.initial_grade" />
              </el-col>
              <el-col :span="12">
                <el-statistic :title="t('optimizeDetail.final') + ' 等级'" :value="result.final_grade" :value-style="{ color: '#67c23a' }" />
              </el-col>
              <el-col :span="12" style="margin-top: 16px;">
                <el-statistic :title="t('optimizeDetail.initial') + ' G2'" :value="result.initial_g2" />
              </el-col>
              <el-col :span="12" style="margin-top: 16px;">
                <el-statistic :title="t('optimizeDetail.final') + ' G2'" :value="result.final_g2" :value-style="{ color: '#67c23a' }" />
              </el-col>
              <el-col :span="24" style="margin-top: 16px;">
                <el-statistic :title="t('optimizeDetail.improvement') + ' (反射线)'" :value="result.final_reflection" :precision="3" />
              </el-col>
            </el-row>
          </div>
          <el-empty v-else-if="status === 'FAILURE'" description="任务失败" />
          <el-empty v-else :description="connState === 'failed' ? '连接失败，请稍后重试' : '等待 WebSocket 消息中...'" />
        </el-card>
      </el-col>

      <el-col v-if="result?.convergence_curve" :span="24">
        <el-card shadow="never" style="margin-top: 20px;">
          <template #header><span>{{ t('optimizeDetail.convergence') }}</span></template>
          <div class="curve-info">
            共 {{ result.convergence_curve.length }} 个数据点 ·
            起始 {{ result.convergence_curve[0]?.toFixed(2) }} → 终止 {{ result.convergence_curve.at(-1)?.toFixed(2) }} ·
            下降 {{ ((1 - result.convergence_curve.at(-1) / result.convergence_curve[0]) * 100).toFixed(2) }}%
          </div>
          <p class="curve-note">W1-D4 SVG 实时渲染将在 W1-D4+ 优化（当前展示数据点摘要）</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.optimize-detail { max-width: 1280px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
.header-row h1 { margin: 0 0 4px; font-size: 22px; }
.header-row .sub { margin: 0; color: #909399; font-size: 13px; }
.header-row code { background: #f4f4f5; padding: 2px 8px; border-radius: 3px; font-family: monospace; }
.conn-state { font-weight: 600; font-size: 12px; margin-left: 8px; }
.curve-info { font-size: 14px; color: #606266; }
.curve-note { color: #909399; font-size: 12px; margin: 8px 0 0; }
</style>
