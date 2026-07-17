/**
 * W1-D4: WebSocket 客户端（断线重连 + 4 消息分发）
 *
 * 用法：
 *   const ws = new OptimizeWS(taskId)
 *   ws.onMessage((msg) => {
 *     // msg.type: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'ERROR'
 *     // msg.progress / current_iter / max_iter / result / error
 *   })
 *   ws.connect()
 *   // ...
 *   ws.close()  // 主动断开（不再重连）
 *
 * 断线重连策略：
 *   - 指数退避：1s / 2s / 4s / 8s / 16s / 30s（封顶）
 *   - 最多重连 8 次（避免无限重试）
 *   - 终态（SUCCESS/FAILURE）自动 close，不再重连
 *   - 主动 close 不重连
 *
 * 后端协议：/api/v1/ws/optimize/{task_id}（M2.5 完工时实现）
 *   - 首条 = DB 快照（PENDING/STARTED）
 *   - 已终态：立即发完整 result 后 close
 *   - 进行中：订阅 Redis pub/sub，转发 STARTED/PROGRESS/SUCCESS/FAILURE
 */
export type WSMessageType =
  | 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'REVOKED' | 'ERROR'

export interface WSProgressMessage {
  type: WSMessageType
  progress?: number          // 0.0 - 1.0
  current_iter?: number
  max_iter?: number
  result?: any               // SUCCESS 时附完整 result（含 convergence_curve）
  error?: string             // FAILURE/ERROR 时附错误信息
}

export type WSMessageHandler = (msg: WSProgressMessage) => void
export type WSStateHandler = (state: WSConnState) => void

export type WSConnState = 'connecting' | 'open' | 'closed' | 'reconnecting' | 'failed'

interface OptimizeWSOptions {
  /** 最大重连次数，默认 8 */
  maxReconnect?: number
  /** 是否启用断线重连，默认 true */
  autoReconnect?: boolean
  /** 退避上限（ms），默认 30000 */
  maxBackoffMs?: number
}

const DEFAULTS: Required<OptimizeWSOptions> = {
  maxReconnect: 8,
  autoReconnect: true,
  maxBackoffMs: 30000,
}

export class OptimizeWS {
  private taskId: string
  private url: string
  private ws: WebSocket | null = null
  private msgHandlers: WSMessageHandler[] = []
  private stateHandlers: WSStateHandler[] = []
  private opts: Required<OptimizeWSOptions>
  private reconnectAttempt = 0
  private reconnectTimer: number | null = null
  private closedByUser = false
  private receivedFinal = false
  private state: WSConnState = 'connecting'

  constructor(taskId: string, options: OptimizeWSOptions = {}) {
    this.taskId = taskId
    this.opts = { ...DEFAULTS, ...options }
    // 自动适配 http/https → ws/wss
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    this.url = `${proto}//${window.location.host}/api/v1/ws/optimize/${taskId}`
  }

  /** 注册消息处理器（可注册多个） */
  onMessage(handler: WSMessageHandler): () => void {
    this.msgHandlers.push(handler)
    return () => {
      const i = this.msgHandlers.indexOf(handler)
      if (i >= 0) this.msgHandlers.splice(i, 1)
    }
  }

  /** 注册连接状态处理器 */
  onStateChange(handler: WSStateHandler): () => void {
    this.stateHandlers.push(handler)
    handler(this.state)
    return () => {
      const i = this.stateHandlers.indexOf(handler)
      if (i >= 0) this.stateHandlers.splice(i, 1)
    }
  }

  /** 启动连接 */
  connect(): void {
    this.closedByUser = false
    this.receivedFinal = false
    this.setState('connecting')
    try {
      this.ws = new WebSocket(this.url)
    } catch (e) {
      console.error('[OptimizeWS] constructor failed:', e)
      this.handleClose()
      return
    }

    this.ws.onopen = () => {
      this.reconnectAttempt = 0
      this.setState('open')
    }

    this.ws.onmessage = (ev) => {
      let msg: WSProgressMessage
      try {
        msg = JSON.parse(ev.data)
      } catch (e) {
        console.warn('[OptimizeWS] parse failed:', e, ev.data)
        return
      }
      this.msgHandlers.forEach((h) => {
        try {
          h(msg)
        } catch (e) {
          console.error('[OptimizeWS] handler error:', e)
        }
      })
      // 终态：自动 close（不再重连）
      if (msg.type === 'SUCCESS' || msg.type === 'FAILURE' || msg.type === 'REVOKED') {
        this.receivedFinal = true
        this.close()
      }
    }

    this.ws.onerror = (ev) => {
      console.warn('[OptimizeWS] error:', ev)
    }

    this.ws.onclose = (ev) => {
      console.info(`[OptimizeWS] closed: code=${ev.code} reason=${ev.reason}`)
      this.ws = null
      this.handleClose()
    }
  }

  /** 主动关闭（不再重连） */
  close(): void {
    this.closedByUser = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      try {
        this.ws.close()
      } catch (e) {
        console.warn('[OptimizeWS] close error:', e)
      }
      this.ws = null
    }
    this.setState('closed')
  }

  private handleClose(): void {
    if (this.closedByUser || this.receivedFinal) {
      this.setState('closed')
      return
    }
    if (!this.opts.autoReconnect) {
      this.setState('failed')
      return
    }
    if (this.reconnectAttempt >= this.opts.maxReconnect) {
      console.warn(`[OptimizeWS] max reconnect (${this.opts.maxReconnect}) reached, giving up`)
      this.setState('failed')
      return
    }
    this.reconnectAttempt++
    const backoff = Math.min(
      this.opts.maxBackoffMs,
      1000 * Math.pow(2, this.reconnectAttempt - 1),
    )
    console.info(`[OptimizeWS] reconnect #${this.reconnectAttempt} in ${backoff}ms`)
    this.setState('reconnecting')
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      if (!this.closedByUser && !this.receivedFinal) {
        this.connect()
      }
    }, backoff)
  }

  private setState(s: WSConnState): void {
    if (this.state === s) return
    this.state = s
    this.stateHandlers.forEach((h) => {
      try {
        h(s)
      } catch (e) {
        console.error('[OptimizeWS] state handler error:', e)
      }
    })
  }

  get currentState(): WSConnState {
    return this.state
  }

  get taskIdValue(): string {
    return this.taskId
  }
}
