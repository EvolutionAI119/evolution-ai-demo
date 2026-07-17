# EVOLUTION AI · 设计令牌（Design Tokens）

> **来源**：W1 完工 DEMO 视频（2026-06-20 预览版）
> **用途**：前端 UI 全局视觉规范，与 M3 视频分镜视觉保持一致
> **维护**：解药（灵感解药）  ·  **审阅**：量子剑客

---

## 1. 色彩系统

### 1.1 主色板

| 令牌 | 色值 | 用途 | 示例 |
|---|---|---|---|
| `--color-bg-primary` | `#0A1628` | 全局深色背景 | 页面底色 |
| `--color-bg-secondary` | `#0F1F3A` | 卡片/容器背景 | 卡片、面板 |
| `--color-bg-tertiary` | `#16294D` | 浮层/弹窗 | 弹窗、tooltip |
| `--color-accent-primary` | `#00D4FF` | 主交互高亮 | 按钮、滑块、链接 |
| `--color-accent-secondary` | `#0099CC` | 次级高亮 | hover、focus |
| `--color-accent-gradient` | `linear-gradient(90deg, #00D4FF, #00FFCC)` | 进度条/数据流 | AI 进度条 |
| `--color-text-primary` | `#FFFFFF` | 主文字 | 标题、正文 |
| `--color-text-secondary` | `#B8C5D6` | 次文字 | 副标题、说明 |
| `--color-text-tertiary` | `#6B7A99` | 辅助文字 | 占位符、disabled |
| `--color-success` | `#00FF88` | 成功状态 | 质检通过 |
| `--color-warning` | `#FFB800` | 警告状态 | 边缘 F5 |
| `--color-error` | `#FF4757` | 错误状态 | F6/F7 失败 |

### 1.2 配色比例

- **深色背景**：70%（bg-primary + bg-secondary）
- **主高亮**：20%（accent-primary）
- **数据色**：10%（success/warning/error + 渐变）

## 2. 字体系统

| 令牌 | 字体 | 用途 |
|---|---|---|
| `--font-mono` | `'JetBrains Mono', 'Source Code Pro', '思源等宽', monospace` | 参数数值、代码、ID |
| `--font-display` | `'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif` | 标题、按钮 |
| `--font-body` | `'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif` | 正文 |
| `--font-size-xs` | `12px` | 辅助说明 |
| `--font-size-sm` | `14px` | 次要文字 |
| `--font-size-base` | `16px` | 正文 |
| `--font-size-lg` | `20px` | 小标题 |
| `--font-size-xl` | `28px` | 大标题 |
| `--font-size-display` | `40px` | 数据展示 |

## 3. 间距与圆角

| 令牌 | 值 | 用途 |
|---|---|---|
| `--space-1` | `4px` | 紧凑间距 |
| `--space-2` | `8px` | 元素内边距 |
| `--space-3` | `16px` | 卡片内边距 |
| `--space-4` | `24px` | 区块间距 |
| `--space-5` | `32px` | 页面间距 |
| `--space-6` | `48px` | 大区块 |
| `--radius-sm` | `4px` | 按钮、输入框 |
| `--radius-md` | `8px` | 卡片 |
| `--radius-lg` | `16px` | 弹窗、大面板 |
| `--radius-full` | `9999px` | 圆形头像/进度环 |

## 4. 阴影与发光

| 令牌 | 值 | 用途 |
|---|---|---|
| `--shadow-sm` | `0 2px 8px rgba(0, 0, 0, 0.3)` | 卡片 |
| `--shadow-md` | `0 4px 16px rgba(0, 0, 0, 0.4)` | 弹窗 |
| `--shadow-lg` | `0 8px 32px rgba(0, 0, 0, 0.5)` | 模态 |
| `--glow-primary` | `0 0 16px rgba(0, 212, 255, 0.5)` | 主按钮 hover |
| `--glow-success` | `0 0 16px rgba(0, 255, 136, 0.5)` | 成功状态 |

## 5. 动效

| 令牌 | 值 | 用途 |
|---|---|---|
| `--duration-fast` | `150ms` | hover/active |
| `--duration-base` | `300ms` | 过渡 |
| `--duration-slow` | `500ms` | 弹窗/页面切换 |
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | 通用 |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 弹性 |
| `--bpm` | `120` | 数据流动画节奏 |

## 6. 关键视觉元素

### 6.1 参数滑块（Designer 页面）

- **轨道**：渐变 `linear-gradient(90deg, #00D4FF, #00FFCC)`
- **滑块**：圆形 + 内部数值气泡
- **状态**：默认 / hover（发光）/ active（放大 1.1x）
- **数值气泡**：深色背景 + 白色文字 + 圆角 4px

### 6.2 AI 进度条（Optimize 页面）

- **渐变色**：`#00D4FF → #00FFCC → #00FF88`
- **流光动画**：从左到右持续 2s 循环
- **分阶段提示**：建模（20%）→ 光顺（50%）→ 质检（80%）→ 导出（100%）
- **百分比文字**：等宽字体，居中

### 6.3 3D 模型

- **材质**：哑光金属，反射率 0.6
- **环境光**：冷色调（#0A1628 主光 + #00D4FF 边光）
- **反射线**：黑/白相间细线，从车头到车尾扫过
- **背景**：暗色 #0A1628，地面带轻微网格

### 6.4 数据仪表盘（Quality 页面）

- **圆形仪表盘**：直径 120px，圆环 8px
- **配色映射**：F5 0-0.1mm 绿 / 0.1-0.3 黄 / >0.3 红
- **数字滚动动画**：从 0 到目标值 1s
- **中心数字**：40px 字体，带单位（mm）

### 6.5 视频分镜卡片（Storyboard 页面）

- **缩略图**：16:9，圆角 8px
- **分镜编号**：左上角，圆形 32x32，#00D4FF
- **时长标签**：右下角，等宽字体
- **hover**：轻微放大 1.02x + 阴影加深

## 7. 应用方式

### 7.1 CSS 变量（推荐）

```css
:root {
  --color-bg-primary: #0A1628;
  --color-accent-primary: #00D4FF;
  --font-mono: 'JetBrains Mono', monospace;
  /* ... */
}
```

### 7.2 Element Plus 主题覆盖

```typescript
// src/styles/element-plus-theme.ts
import { defineConfig } from 'element-plus'

export const elementPlusTheme = defineConfig({
  '--el-color-primary': '#00D4FF',
  '--el-bg-color': '#0A1628',
  '--el-text-color-primary': '#FFFFFF',
  // ...
})
```

### 7.3 Three.js 场景

```typescript
// src/three/scene-config.ts
export const sceneConfig = {
  background: '#0A1628',
  ambient: { color: '#16294D', intensity: 0.4 },
  directional: { color: '#00D4FF', intensity: 0.8 },
  material: { metalness: 0.6, roughness: 0.3 },
}
```

---

## 8. 验收标准

- [ ] W1-D3 完成的 7 个页面 100% 符合本设计令牌
- [ ] Element Plus 主题覆盖完成
- [ ] Three.js 场景配置完成
- [ ] 与 W1 完工 DEMO 视频视觉一致（主人验收）
- [ ] W2-D4 完成的视频分镜页面与 DEMO 视频风格统一

---

**维护规则**：
- 任何视觉变更需主人验收后再写入本档
- 视频项目产出后必须同步更新视觉规范
- 不要在 src/ 中散落颜色值，统一引用本档令牌
