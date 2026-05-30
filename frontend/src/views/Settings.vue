<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold">系统设置</h1>
      <p class="text-gray-500">管理您的账户安全、通知偏好和隐私设置</p>
    </div>

    <!-- 账户安全设置 -->
    <div class="bg-white rounded-lg shadow-sm border p-6 mb-6 hover:shadow-md transition-shadow">
      <h2 class="text-lg font-bold mb-4 pb-2 border-b flex items-center gap-2">
        <i class="fa fa-shield text-primary"></i>
        <span>账户安全</span>
      </h2>

      <div class="space-y-4">
        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">登录密码</h3>
              <p class="text-sm text-gray-500 mt-0.5">定期更换密码保障账户安全</p>
            </div>
            <router-link to="/edit-password" class="text-primary hover:text-primary/80 text-sm flex items-center gap-1">
              <span>修改密码</span>
              <i class="fa fa-chevron-right text-xs"></i>
            </router-link>
          </div>
        </div>

        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">邮箱验证</h3>
              <p class="text-sm text-gray-500 mt-0.5">{{ userStore.userInfo?.email || '未设置邮箱' }}</p>
            </div>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              已验证
            </span>
          </div>
        </div>

        <div class="py-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">登录历史</h3>
              <p class="text-sm text-gray-500 mt-0.5">查看最近的登录记录和设备信息</p>
            </div>
            <button @click="showLoginHistory" class="text-primary hover:text-primary/80 text-sm flex items-center gap-1">
              <span>查看详情</span>
              <i class="fa fa-chevron-right text-xs"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 通知设置 -->
    <div class="bg-white rounded-lg shadow-sm border p-6 mb-6 hover:shadow-md transition-shadow">
      <h2 class="text-lg font-bold mb-4 pb-2 border-b flex items-center gap-2">
        <i class="fa fa-bell text-primary"></i>
        <span>通知偏好</span>
      </h2>

      <div class="space-y-4">
        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">组会提醒</h3>
              <p class="text-sm text-gray-500 mt-0.5">组会开始前收到提醒通知</p>
            </div>
            <ToggleSwitch v-model="settings.meetingReminder" @change="saveSettings" />
          </div>
        </div>

        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">组会变更通知</h3>
              <p class="text-sm text-gray-500 mt-0.5">组会时间、地点变更时收到通知</p>
            </div>
            <ToggleSwitch v-model="settings.meetingChangeNotification" @change="saveSettings" />
          </div>
        </div>

        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">导师消息通知</h3>
              <p class="text-sm text-gray-500 mt-0.5">收到导师发送的消息时通知</p>
            </div>
            <ToggleSwitch v-model="settings.teacherMessageNotification" @change="saveSettings" />
          </div>
        </div>

        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">系统公告</h3>
              <p class="text-sm text-gray-500 mt-0.5">接收实验室发布的系统公告</p>
            </div>
            <ToggleSwitch v-model="settings.systemAnnouncement" @change="saveSettings" />
          </div>
        </div>

        <div class="py-4">
          <div>
            <h3 class="font-medium mb-3">通知方式</h3>
            <div class="space-y-3">
              <div class="flex items-center gap-3">
                <ToggleSwitch v-model="settings.notifyBySystem" @change="saveSettings" />
                <span class="text-sm">系统内消息</span>
              </div>
              <div class="flex items-center gap-3">
                <ToggleSwitch v-model="settings.notifyByEmail" @change="saveSettings" />
                <span class="text-sm">电子邮件</span>
              </div>
              <div class="flex items-center gap-3">
                <ToggleSwitch v-model="settings.notifyBySMS" @change="saveSettings" />
                <span class="text-sm">手机短信</span>
                <p class="text-xs text-gray-500">(需绑定手机号)</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 隐私设置 -->
    <div class="bg-white rounded-lg shadow-sm border p-6 mb-6 hover:shadow-md transition-shadow">
      <h2 class="text-lg font-bold mb-4 pb-2 border-b flex items-center gap-2">
        <i class="fa fa-lock text-primary"></i>
        <span>隐私设置</span>
      </h2>

      <div class="space-y-4">
        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">个人资料可见范围</h3>
              <p class="text-sm text-gray-500 mt-0.5">控制谁可以查看您的个人资料信息</p>
            </div>
            <select v-model="settings.profileVisibility" @change="saveSettings"
                    class="bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 w-full sm:w-auto">
              <option value="all">实验室所有成员</option>
              <option value="advisor">仅导师和管理员</option>
              <option value="group">仅同研究组成员</option>
            </select>
          </div>
        </div>

        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">联系方式可见性</h3>
              <p class="text-sm text-gray-500 mt-0.5">控制是否公开您的邮箱和电话</p>
            </div>
            <ToggleSwitch v-model="settings.contactVisibility" @change="saveSettings" />
          </div>
        </div>

        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">研究成果可见性</h3>
              <p class="text-sm text-gray-500 mt-0.5">控制是否公开您的论文和项目成果</p>
            </div>
            <ToggleSwitch v-model="settings.researchVisibility" @change="saveSettings" />
          </div>
        </div>

        <div class="py-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">活动记录</h3>
              <p class="text-sm text-gray-500 mt-0.5">是否允许记录您的系统使用活动</p>
            </div>
            <ToggleSwitch v-model="settings.activityLog" @change="saveSettings" />
          </div>
        </div>
      </div>
    </div>

    <!-- 账户管理 -->
    <div class="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
      <h2 class="text-lg font-bold mb-4 pb-2 border-b flex items-center gap-2">
        <i class="fa fa-user-circle text-primary"></i>
        <span>账户管理</span>
      </h2>

      <div class="space-y-4">
        <div class="py-4 border-b border-gray-50">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium">账号绑定</h3>
              <p class="text-sm text-gray-500 mt-0.5">绑定其他账号用于快捷登录</p>
            </div>
            <div class="flex gap-2">
              <button class="w-8 h-8 rounded-full bg-[#E4E6EB] flex items-center justify-center text-gray-600 hover:bg-[#DADDE1] transition-colors">
                <i class="fa fa-qq"></i>
              </button>
              <button class="w-8 h-8 rounded-full bg-[#07C160] flex items-center justify-center text-white hover:bg-[#00B450] transition-colors">
                <i class="fa fa-weixin"></i>
              </button>
            </div>
          </div>
        </div>

        <div class="py-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="font-medium text-red-500">注销账户</h3>
              <p class="text-sm text-gray-500 mt-0.5">注销后所有数据将不可恢复，请谨慎操作</p>
            </div>
            <button @click="showDeleteModal = true" class="text-red-500 hover:text-red-500/80 text-sm border border-red-500/30 px-3 py-1.5 rounded-lg hover:bg-red-500/5 transition-colors">
              注销账户
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 注销账户确认弹窗 -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div class="p-6 border-b border-gray-100">
          <h3 class="text-lg font-bold text-gray-800">确认注销账户</h3>
          <p class="text-sm text-gray-500 mt-2">您确定要注销当前账户吗？此操作不可撤销，注销后您的所有数据将被永久删除。</p>
        </div>
        <div class="p-4 flex justify-end gap-3">
          <button @click="showDeleteModal = false" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm">
            取消
          </button>
          <button @click="deleteAccount" class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-500/90 transition-colors text-sm">
            确认注销
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import ToggleSwitch from '../components/ToggleSwitch.vue'

const userStore = useUserStore()

const showDeleteModal = ref(false)

const settings = ref({
  meetingReminder: true,
  meetingChangeNotification: true,
  teacherMessageNotification: true,
  systemAnnouncement: true,
  notifyBySystem: true,
  notifyByEmail: true,
  notifyBySMS: false,
  profileVisibility: 'all',
  contactVisibility: true,
  researchVisibility: true,
  activityLog: true
})

function saveSettings() {
  // 保存设置到 localStorage
  localStorage.setItem('user_settings', JSON.stringify(settings.value))
  window.$toast?.('设置已更新', 'success')
}

function loadSettings() {
  const saved = localStorage.getItem('user_settings')
  if (saved) {
    settings.value = { ...settings.value, ...JSON.parse(saved) }
  }
}

function showLoginHistory() {
  window.$toast?.('登录历史：最近登录于今天 (本机浏览器)', 'info')
}

function deleteAccount() {
  showDeleteModal.value = false
  window.$toast?.('账户注销功能暂未开放', 'warning')
}

onMounted(loadSettings)
</script>