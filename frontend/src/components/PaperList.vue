<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <div class="p-6 border-b flex justify-between items-center">
      <h2 class="font-bold text-lg">{{ title }}</h2>
      <router-link to="/paper-database" class="bg-primary text-white px-3 py-1.5 rounded-lg hover:bg-primary/90 text-sm flex items-center gap-1">
        <i class="fa fa-plus"></i> 添加文献
      </router-link>
    </div>
    <div class="p-4">
      <div v-if="loading" class="text-center text-gray-500 py-4">
        <i class="fa fa-spinner fa-spin mr-2"></i>加载中...
      </div>
      <div v-else-if="!papers.length" class="text-center text-gray-500 py-4">暂无文献</div>
      <div v-else class="space-y-4">
        <div v-for="p in papers" :key="p.id" class="border border-gray-100 rounded-lg p-3 hover:shadow-sm">
          <div class="flex justify-between items-start">
            <h3 class="font-medium text-primary hover:underline cursor-pointer">{{ p.title }}</h3>
            <span class="text-xs bg-gray-100 px-2 py-0.5 rounded">{{ p.year || '未知' }}</span>
          </div>
          <p class="text-sm text-gray-600 mt-1">{{ p.authors || '未知作者' }}</p>
          <p class="text-xs text-gray-500 mt-1 line-clamp-2">{{ abstractText(p.abstract) }}</p>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <span v-if="p.journal" class="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{{ p.journal }}</span>
            <div class="ml-auto flex items-center gap-2">
              <span class="text-gray-500 text-xs"><i class="fa fa-download"></i> {{ p.download_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="mt-4 text-center">
        <router-link to="/paper-database" class="text-primary text-sm hover:underline">浏览更多文献</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: String,
  papers: { type: Array, default: [] },
  loading: { type: Boolean, default: false }
})

function abstractText(abstract) {
  if (!abstract) return '暂无摘要'
  return abstract.length > 100 ? abstract.substring(0, 100) + '...' : abstract
}
</script>