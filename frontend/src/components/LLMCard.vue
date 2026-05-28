<template>
  <div class="border border-gray-100 rounded-lg p-4 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 flex items-start gap-3">
    <div :class="`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center flex-shrink-0 shadow-sm`">
      <span class="text-white font-bold text-lg">{{ icon }}</span>
    </div>
    <div class="flex-1">
      <h4 class="font-semibold mb-1">{{ title }}</h4>
      <p class="text-gray-600 text-sm mb-2">{{ desc }}</p>
      <a :href="url" target="_blank" class="inline-flex items-center text-purple-600 text-sm font-medium hover:underline">
        访问网站 <i class="fa fa-external-link ml-1"></i>
      </a>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  desc: String,
  url: String,
  icon: String,
  gradient: String
})
</script>