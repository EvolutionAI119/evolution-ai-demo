/**
 * Project Store（M3 W1-D1 骨架）
 *
 * 状态：
 * - projects: 方案列表
 * - current: 当前选中
 * - loading / error
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Project, ProjectListResponse, ProjectCreateRequest } from '@/types/api'
import { listProjects, createProject, deleteProject, getProject } from '@/api/project'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const current = ref<Project | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)

  const hasProjects = computed(() => projects.value.length > 0)

  async function fetchList(page = 1, pageSize = 20): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const resp: ProjectListResponse = await listProjects(page, pageSize)
      projects.value = resp.items
      total.value = resp.total
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: number): Promise<void> {
    loading.value = true
    error.value = null
    try {
      current.value = await getProject(id)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function create(req: ProjectCreateRequest): Promise<Project | null> {
    loading.value = true
    error.value = null
    try {
      const p = await createProject(req)
      await fetchList()
      return p
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      loading.value = false
    }
  }

  async function remove(id: number): Promise<boolean> {
    try {
      await deleteProject(id)
      projects.value = projects.value.filter((p) => p.id !== id)
      if (current.value?.id === id) current.value = null
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    }
  }

  return {
    projects,
    current,
    loading,
    error,
    total,
    hasProjects,
    fetchList,
    fetchOne,
    create,
    remove,
  }
})
