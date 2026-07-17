/**
 * Vue Router 配置（W1-D3 扩展）
 *
 * 5 大业务页面 + 首页 + 4 个 :id 详情子页 + 2 个错误页
 * - /                       首页
 * - /designer               造型设计（参数编辑 + 实时预览）
 * - /quality                质量评估
 * - /optimize               AI 优化列表
 * - /optimize/:taskId       优化任务详情（WS 实时进度）
 * - /storyboard             分镜脚本列表
 * - /storyboard/:projectId  分镜项目详情
 * - /projects               方案管理列表
 * - /projects/:projectId    项目详情（5 tab：概览/3D/优化/质检/分镜）
 * - /404                    未找到
 * - /500                    服务错误
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/designer',
    name: 'designer',
    component: () => import('@/views/Designer.vue'),
    meta: { title: '造型设计' },
  },
  {
    path: '/quality',
    name: 'quality',
    component: () => import('@/views/Quality.vue'),
    meta: { title: '质量评估' },
  },
  {
    path: '/optimize',
    name: 'optimize',
    component: () => import('@/views/Optimize.vue'),
    meta: { title: 'AI 优化' },
  },
  {
    path: '/optimize/:taskId',
    name: 'optimize-detail',
    component: () => import('@/views/OptimizeDetail.vue'),
    meta: { title: '优化任务详情' },
  },
  {
    path: '/storyboard',
    name: 'storyboard',
    component: () => import('@/views/Storyboard.vue'),
    meta: { title: '分镜脚本' },
  },
  {
    path: '/storyboard/:projectId',
    name: 'storyboard-detail',
    component: () => import('@/views/StoryboardDetail.vue'),
    meta: { title: '分镜项目详情' },
  },
  {
    path: '/projects',
    name: 'projects',
    component: () => import('@/views/Projects.vue'),
    meta: { title: '方案管理' },
  },
  {
    path: '/projects/:projectId',
    name: 'project-detail',
    component: () => import('@/views/ProjectDetail.vue'),
    meta: { title: '项目详情' },
  },
  {
    path: '/404',
    name: 'not-found',
    component: () => import('@/views/errors/NotFound.vue'),
    meta: { title: '页面未找到' },
  },
  {
    path: '/500',
    name: 'server-error',
    component: () => import('@/views/errors/ServerError.vue'),
    meta: { title: '服务器错误' },
  },
  {
    // 兜底：未匹配路由跳 404
    path: '/:pathMatch(.*)*',
    redirect: '/404',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  const baseTitle = 'EVOLUTION AI'
  const subTitle = to.meta.title as string | undefined
  document.title = subTitle ? `${subTitle} · ${baseTitle}` : baseTitle
})

export default router
