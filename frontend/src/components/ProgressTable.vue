<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-8">
    <div class="p-6 border-b">
      <h2 class="font-bold text-lg">学生研究进展</h2>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[800px]">
        <thead>
          <tr class="bg-gray-50">
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">学生</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">研究方向</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">最近进展</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">下次目标</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">最后更新</th>
            <th class="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-if="loading">
            <td colspan="6" class="px-6 py-8 text-center text-gray-500">
              <i class="fa fa-spinner fa-spin mr-2"></i>加载中...
            </td>
          </tr>
          <tr v-else-if="!progress.length">
            <td colspan="6" class="px-6 py-8 text-center text-gray-500">
              <i class="fa fa-inbox text-3xl mb-2"></i>
              <p>暂无学生研究进展数据</p>
            </td>
          </tr>
          <tr v-for="p in progress" :key="p.user_id">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <img :src="avatarUrl(p)" class="w-8 h-8 rounded-full mr-3 object-cover">
                <div>
                  <p class="font-medium text-sm">{{ p.username }}</p>
                  <p class="text-xs text-gray-500">{{ p.degree_text || '学生' }}</p>
                </div>
              </div>
            </td>
            <td class="px-6 py-4">
              <p class="text-sm">{{ p.research_direction || p.user_research_direction || '暂无方向' }}</p>
            </td>
            <td class="px-6 py-4">
              <p class="text-sm line-clamp-2">{{ truncate(p.weekly_progress || '暂无进展记录', 50) }}</p>
            </td>
            <td class="px-6 py-4">
              <p class="text-sm line-clamp-2">{{ truncate(p.next_goal || '暂无目标', 50) }}</p>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(p.submission_date) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm">
              <router-link :to="`/research-progress?user_id=${p.user_id}`" class="text-primary hover:text-primary/80 mr-3">详情</router-link>
              <router-link :to="`/research-progress?user_id=${p.user_id}`" class="bg-primary/10 text-primary px-3 py-1 rounded hover:bg-primary/20 text-sm">沟通</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="p-4 border-t text-center">
      <router-link to="/research-progress" class="text-primary text-sm hover:underline">查看所有学生进展</router-link>
    </div>
  </div>
</template>

<script setup>
import { getAvatarUrl } from '../config'

const props = defineProps({
  progress: { type: Array, default: [] },
  loading: { type: Boolean, default: false }
})

function avatarUrl(p) {
  return getAvatarUrl(p.avatar, p.username || 'User')
}

function truncate(text, len) {
  if (!text) return '暂无'
  return text.length > len ? text.substring(0, len) + '...' : text
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : '未更新'
}
</script>