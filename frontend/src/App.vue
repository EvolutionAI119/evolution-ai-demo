<script setup lang="ts">
/**
 * M3 W1-D2 根组件
 * - 顶部导航栏（i18n 化）
 * - 语言切换按钮（中/英）
 * - <router-view> 内容区
 */
import { useRoute } from 'vue-router'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale, SUPPORTED_LOCALES, type Locale } from './i18n'

const { t, locale } = useI18n()
const route = useRoute()
const activeMenu = computed(() => route.path)

// nav 配置：path 不变，label 用 i18n key
const navItems = [
  { path: '/', labelKey: 'app.nav.home', icon: 'House' },
  { path: '/designer', labelKey: 'app.nav.designer', icon: 'Brush' },
  { path: '/quality', labelKey: 'app.nav.quality', icon: 'DataAnalysis' },
  { path: '/optimize', labelKey: 'app.nav.optimize', icon: 'MagicStick' },
  { path: '/storyboard', labelKey: 'app.nav.storyboard', icon: 'VideoCamera' },
  { path: '/projects', labelKey: 'app.nav.projects', icon: 'Folder' },
] as const

// 当前语言 + 切换处理
const currentLocale = computed<Locale>(() => (locale.value as Locale) || 'zh-CN')

function toggleLocale() {
  const idx = SUPPORTED_LOCALES.indexOf(currentLocale.value)
  const next = SUPPORTED_LOCALES[(idx + 1) % SUPPORTED_LOCALES.length]
  setLocale(next)
}
</script>

<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="header-brand">
        <el-icon :size="22" color="#409eff"><Lightning /></el-icon>
        <span class="title">{{ t('app.name') }}</span>
        <el-tag size="small" type="info" effect="plain" round>{{ t('app.version') }}</el-tag>
      </div>
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        :ellipsis="false"
        router
        class="nav-menu"
      >
        <el-menu-item
          v-for="item in navItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ t(item.labelKey) }}</span>
        </el-menu-item>
      </el-menu>
      <div class="header-actions">
        <el-tooltip :content="t('app.lang.switchTip')" placement="bottom">
          <el-button
            :icon="currentLocale === 'zh-CN' ? 'Position' : 'Position'"
            size="small"
            plain
            @click="toggleLocale"
            class="lang-btn"
            :title="t('app.lang.switchTip')"
          >
            {{ currentLocale === 'zh-CN' ? t('app.lang.en') : t('app.lang.zh') }}
          </el-button>
        </el-tooltip>
      </div>
    </el-header>

    <el-main class="main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.header {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  padding: 0 32px;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 24px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.header-brand .title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.nav-menu {
  flex: 1;
  border-bottom: none !important;
}

.header-actions {
  flex-shrink: 0;
}

.lang-btn {
  font-weight: 500;
  min-width: 64px;
}

.main {
  background: #f5f7fa;
  padding: 24px 32px;
  min-height: calc(100vh - 60px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
