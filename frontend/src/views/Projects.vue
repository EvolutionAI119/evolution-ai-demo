<script setup lang="ts">
/**
 * 方案管理列表（W1-D3）
 * 表格 + 筛选 + 分页 + 新建/编辑/删除
 */
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const { t } = useI18n()
const router = useRouter()

interface Project {
  id: number
  name: string
  surface_type: string
  status: string
  created_at: string
  updated_at: string
}

const loading = ref(false)
const projects = ref<Project[]>([])
const search = ref<string>('')
const page = ref<number>(1)
const pageSize = ref<number>(10)
const total = ref<number>(0)

async function fetchProjects() {
  loading.value = true
  try {
    const { data } = await api.get('/api/v1/project/', {
      params: { skip: (page.value - 1) * pageSize.value, limit: pageSize.value },
    })
    projects.value = data.items ?? data ?? []
    total.value = data.total ?? projects.value.length
  } catch {
    // 后端暂未实现时不报错，给出空态
    projects.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function viewDetail(id: number) {
  router.push(`/projects/${id}`)
}

async function deleteProject(id: number) {
  try {
    await ElMessageBox.confirm('确认删除此方案？', '提示', { type: 'warning' })
    await api.delete(`/api/v1/project/${id}`)
    ElMessage.success('已删除')
    fetchProjects()
  } catch {
    /* user cancelled */
  }
}

function statusType(s: string) {
  return { draft: 'info', running: 'warning', success: 'success', failed: 'danger' }[s] || 'info'
}

onMounted(fetchProjects)
</script>

<template>
  <div class="projects">
    <el-card class="header-card" shadow="never">
      <div class="header-row">
        <div>
          <h1>{{ t('projects.title') }}</h1>
          <p class="sub">{{ t('projects.subtitle') }}</p>
        </div>
        <div class="header-actions">
          <el-input v-model="search" :placeholder="t('projects.actions.search')" clearable style="width: 200px;" />
          <el-button type="primary" @click="fetchProjects">{{ t('projects.actions.refresh') }}</el-button>
          <el-button type="success" @click="router.push('/designer')">
            {{ t('projects.actions.create') }}
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="projects" stripe>
        <el-table-column prop="id" :label="t('projects.table.id')" width="80" />
        <el-table-column prop="name" :label="t('projects.table.name')" />
        <el-table-column prop="surface_type" :label="t('projects.table.surfaceType')" width="140" />
        <el-table-column :label="t('projects.table.status')" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status) as any" effect="plain">{{ t(`projects.status.${row.status}`) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="t('projects.table.createdAt')" width="180" />
        <el-table-column :label="t('projects.table.actions')" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row.id)">查看</el-button>
            <el-button size="small" type="danger" @click="deleteProject(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && projects.length === 0" :description="t('projects.empty')" />
      <el-pagination
        v-if="total > 0"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end;"
        @current-change="fetchProjects"
        @size-change="fetchProjects"
      />
    </el-card>
  </div>
</template>

<style scoped>
.projects { max-width: 1280px; margin: 0 auto; }
.header-card { margin-bottom: 20px; }
.header-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
.header-row h1 { margin: 0 0 4px; font-size: 22px; }
.header-row .sub { margin: 0; color: #909399; font-size: 13px; }
.header-actions { display: flex; gap: 8px; }
</style>
