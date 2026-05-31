<template>
  <div class="p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">
        {{ userStore.role === 'student' ? '我的研究进展' : '研究进展管理' }}
      </h1>
      <p class="text-gray-500">
        {{ userStore.role === 'student' ? '记录和追踪你的研究进度' : '跟踪和管理团队成员的研究进展' }}
      </p>
    </div>

    <!-- 学生视图 -->
    <div v-if="userStore.role === 'student'">
      <!-- 标签切换 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
        <div class="flex gap-4">
          <button @click="switchTab('my')" :class="tabClass('my')">我的进展</button>
          <button @click="switchTab('team')" :class="tabClass('team')">团队进展</button>
        </div>
      </div>

      <!-- 我的进展区域 -->
      <div v-show="activeTab === 'my'">
        <!-- 提交周期信息 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <p class="text-gray-600">当前周期：<span class="font-medium text-primary">{{ periodText(mySettings?.period_type) }}</span></p>
              <p class="text-gray-500 text-sm">提醒天数：<span>{{ mySettings?.reminder_days || 3 }}天</span></p>
            </div>
            <button @click="openSubmitModal" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 flex items-center gap-2 transition-colors">
              <i class="fa fa-plus"></i><span>提交本周进展</span>
            </button>
          </div>
        </div>

        <!-- 最新进展 -->
        <div v-if="latestProgress" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-800">
              <i class="fa fa-star text-yellow-500 mr-2"></i>最新进展
            </h3>
            <div class="flex gap-2">
              <button @click="viewDetail(latestProgress.id)" class="px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary hover:text-white transition-all">
                <i class="fa fa-eye mr-1"></i>查看详情
              </button>
              <button @click="editProgress(latestProgress.id)" class="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-500 hover:text-white transition-all">
                <i class="fa fa-edit mr-1"></i>更新进展
              </button>
            </div>
          </div>
          <div class="space-y-3">
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <i class="fa fa-file-text-o text-primary"></i>
              </div>
              <div class="flex-1">
                <p class="font-semibold text-gray-800">{{ latestProgress.research_direction }}</p>
                <p class="text-sm text-gray-500">提交时间：{{ formatDate(latestProgress.created_at) }}</p>
              </div>
              <span :class="statusBadgeClass(latestProgress.status || 'normal')">{{ statusText(latestProgress.status || 'normal') }}</span>
            </div>
            <div class="bg-gray-50 rounded-lg p-3 space-y-2">
              <p class="text-sm text-gray-600"><strong>本周进展：</strong>{{ latestProgress.weekly_progress }}</p>
              <p class="text-sm text-gray-600"><strong>下周计划：</strong>{{ latestProgress.next_goal || '-' }}</p>
              <p class="text-sm text-gray-600"><strong>完成度：</strong>{{ latestProgress.completion_rate }}%</p>
            </div>
            <div v-if="latestProgress.supervisor_feedback" class="p-3 bg-blue-50 rounded-lg">
              <p class="text-sm text-gray-500 mb-1">导师反馈：</p>
              <p class="text-gray-700">{{ latestProgress.supervisor_feedback }}</p>
            </div>
          </div>
        </div>

        <!-- 历史进展 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
            <h3 class="text-lg font-semibold text-gray-800">历史进展记录</h3>
            <div class="flex items-center gap-2 w-full sm:w-auto">
              <div class="relative flex-1 sm:flex-initial">
                <input v-model="mySearchKeyword" type="text" class="w-full sm:w-64 px-4 py-2 pl-10 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary" placeholder="搜索进展内容...">
                <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
              </div>
            </div>
          </div>
          <div id="history-progress-list">
            <div v-if="filteredHistory.length > 0" class="space-y-4">
              <div v-for="item in paginatedHistory" :key="item.id" class="progress-item border border-gray-100">
                <div class="flex justify-between items-start mb-2">
                  <div>
                    <p class="font-semibold text-gray-800">{{ item.research_direction }}</p>
                    <p class="text-sm text-gray-500">{{ formatDate(item.created_at) }}</p>
                  </div>
                  <span :class="statusBadgeClass(item.status || 'normal')">{{ statusText(item.status || 'normal') }}</span>
                </div>
                <p class="text-sm text-gray-600 mb-1"><span class="font-medium text-gray-700">本周进展：</span>{{ item.weekly_progress }}</p>
                <p v-if="item.difficulties" class="text-sm text-orange-600 mb-2"><span class="font-medium text-gray-700">遇到的困难：</span>{{ item.difficulties }}</p>
                <p v-if="item.next_goal" class="text-sm text-gray-600 mb-2"><span class="font-medium text-gray-700">下周计划：</span>{{ item.next_goal }}</p>
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2 text-sm text-gray-500">
                    <span>完成度：{{ item.completion_rate }}%</span>
                  </div>
                  <div class="flex gap-2">
                    <button @click="viewDetail(item.id)" class="px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary hover:text-white transition-all">
                      <i class="fa fa-eye mr-1"></i>查看详情
                    </button>
                    <button @click="editProgress(item.id)" class="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-500 hover:text-white transition-all">
                      <i class="fa fa-edit mr-1"></i>编辑
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center text-gray-500 py-8">
              <i class="fa fa-inbox text-4xl mb-4"></i>
              <p>暂无进展记录</p>
              <p class="text-sm">点击上方按钮开始提交你的研究进展</p>
            </div>
          </div>
          <!-- 分页 -->
          <div v-if="filteredHistory.length > 0" class="px-6 py-4 bg-gray-50 border-t border-gray-200 -mx-6 -mb-6 mt-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-2">
                  <label class="text-sm text-gray-600">每页显示</label>
                  <select v-model="myPerPage" class="px-3 py-1 border border-gray-300 rounded-lg text-sm">
                    <option value="10">10条</option>
                    <option value="20">20条</option>
                    <option value="50">50条</option>
                  </select>
                </div>
                <div class="text-sm text-gray-600">共 {{ filteredHistory.length }} 条</div>
              </div>
              <div class="flex items-center gap-2">
                <button @click="myCurrentPage--" :disabled="myCurrentPage === 1" class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50">
                  <i class="fa fa-chevron-left mr-1"></i>上一页
                </button>
                <span class="px-3 py-1 text-sm text-gray-600">第 {{ myCurrentPage }} 页</span>
                <button @click="myCurrentPage++" :disabled="myCurrentPage >= myTotalPages" class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50">
                  下一页<i class="fa fa-chevron-right ml-1"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 团队进展区域 -->
      <div v-show="activeTab === 'team'">
        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-lg p-4 border border-gray-100">
            <div class="flex items-center justify-between">
              <div><p class="text-gray-500 text-sm">总人数</p><h3 class="text-2xl font-bold mt-1">{{ studentTeamStats.total_students || 0 }}</h3></div>
              <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-primary">
                <i class="fa fa-users"></i>
              </div>
            </div>
          </div>
          <div class="bg-white rounded-lg p-4 border border-gray-100">
            <div class="flex items-center justify-between">
              <div><p class="text-gray-500 text-sm">进度正常</p><h3 class="text-2xl font-bold mt-1 text-green-600">{{ studentTeamStats.normal_count || 0 }}</h3></div>
              <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600">
                <i class="fa fa-check-circle"></i>
              </div>
            </div>
          </div>
          <div class="bg-white rounded-lg p-4 border border-gray-100">
            <div class="flex items-center justify-between">
              <div><p class="text-gray-500 text-sm">进度预警</p><h3 class="text-2xl font-bold mt-1 text-yellow-600">{{ (studentTeamStats.warning_count || 0) + (studentTeamStats.delayed_count || 0) }}</h3></div>
              <div class="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center text-yellow-600">
                <i class="fa fa-exclamation-circle"></i>
              </div>
            </div>
          </div>
          <div class="bg-white rounded-lg p-4 border border-gray-100">
            <div class="flex items-center justify-between">
              <div><p class="text-gray-500 text-sm">未更新本周</p><h3 class="text-2xl font-bold mt-1 text-gray-600">{{ studentTeamStats.not_updated_count || 0 }}</h3></div>
              <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600">
                <i class="fa fa-times-circle"></i>
              </div>
            </div>
          </div>
        </div>

        <!-- 筛选工具栏 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
          <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div class="flex flex-wrap gap-2">
              <button @click="studentFilter = 'all'" :class="filterBtnClass('all')">全部成员</button>
              <button @click="studentFilter = 'doctoral'" :class="filterBtnClass('doctoral')">博士</button>
              <button @click="studentFilter = 'master'" :class="filterBtnClass('master')">硕士</button>
              <button @click="studentFilter = 'undergraduate'" :class="filterBtnClass('undergraduate')">本科</button>
              <button @click="studentFilter = 'normal'" :class="filterBtnClass('normal')">进度正常</button>
              <button @click="studentFilter = 'warning'" :class="filterBtnClass('warning')">进度预警</button>
            </div>
            <div class="relative sm:ml-auto sm:max-w-xs">
              <input v-model="studentSearchKeyword" type="text" class="w-full px-4 py-2 pl-10 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/30" placeholder="搜索学生姓名、研究方向...">
              <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
            </div>
          </div>
        </div>

        <!-- 团队进展表格 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="p-6 border-b border-gray-100">
            <h3 class="text-lg font-semibold text-gray-800">团队研究进展</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-gray-50 text-left text-sm text-gray-500">
                <tr>
                  <th class="px-6 py-4 font-medium">学生</th>
                  <th class="px-6 py-4 font-medium">研究方向</th>
                  <th class="px-6 py-4 font-medium">最新进展</th>
                  <th class="px-6 py-4 font-medium">状态</th>
                  <th class="px-6 py-4 font-medium">最后更新</th>
                  <th class="px-6 py-4 font-medium">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100 text-sm">
                <tr v-for="item in filteredStudentTeamList" :key="item.user_id">
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      <img :src="getAvatarUrl(item.avatar, item.username)" class="w-8 h-8 rounded-full object-cover">
                      <span>{{ item.username }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4 text-gray-600">{{ item.research_direction || '-' }}</td>
                  <td class="px-6 py-4 text-gray-600 max-w-xs truncate">{{ item.weekly_progress || '-' }}</td>
                  <td class="px-6 py-4">
                    <span :class="statusBadgeClass(item.computed_status || item.status || 'normal')">{{ statusText(item.computed_status || item.status || 'normal') }}</span>
                  </td>
                  <td class="px-6 py-4 text-gray-500">{{ formatDate(item.submission_date) }}</td>
                  <td class="px-6 py-4">
                    <button v-if="item.progress_id" @click="viewDetail(item.progress_id)" class="w-8 h-8 bg-primary/10 text-primary rounded-lg hover:bg-primary hover:text-white transition-all flex items-center justify-center" title="查看详情">
                      <i class="fa fa-eye"></i>
                    </button>
                    <span v-else class="text-gray-400 text-sm">暂无进展</span>
                  </td>
                </tr>
                <tr v-if="filteredStudentTeamList.length === 0">
                  <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                    <i class="fa fa-inbox text-4xl mb-4"></i>
                    <p>暂无团队进展数据</p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- 分页 -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-2">
                  <label class="text-sm text-gray-600">每页显示</label>
                  <select v-model="studentPerPage" @change="fetchStudentTeamProgress()" class="px-3 py-1 border border-gray-300 rounded-lg text-sm">
                    <option value="10">10条</option>
                    <option value="20">20条</option>
                    <option value="50">50条</option>
                  </select>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button @click="studentCurrentPage--; fetchStudentTeamProgress()" :disabled="studentCurrentPage === 1" class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50">
                  <i class="fa fa-chevron-left mr-1"></i>上一页
                </button>
                <span class="px-3 py-1 text-sm text-gray-600">第 {{ studentCurrentPage }} 页</span>
                <button @click="studentCurrentPage++; fetchStudentTeamProgress()" :disabled="studentCurrentPage >= studentTotalPages" class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50">
                  下一页<i class="fa fa-chevron-right ml-1"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 导师/管理员视图 -->
    <div v-else>
      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-lg p-4 border border-gray-100">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">总人数</p><h3 class="text-2xl font-bold mt-1">{{ teamStats.total_students || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-primary">
              <i class="fa fa-users"></i>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border border-gray-100">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">进度正常</p><h3 class="text-2xl font-bold mt-1 text-green-600">{{ teamStats.normal_count || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600">
              <i class="fa fa-check-circle"></i>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border border-gray-100">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">进度预警</p><h3 class="text-2xl font-bold mt-1 text-yellow-600">{{ (teamStats.warning_count || 0) + (teamStats.delayed_count || 0) }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center text-yellow-600">
              <i class="fa fa-exclamation-circle"></i>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border border-gray-100">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">未更新本周</p><h3 class="text-2xl font-bold mt-1 text-gray-600">{{ teamStats.not_updated_count || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600">
              <i class="fa fa-times-circle"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- 筛选工具栏 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
        <div class="mb-4">
          <div class="relative">
            <input v-model="teamSearchKeyword" type="text" class="w-full px-4 py-2 pl-10 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/30" placeholder="搜索学生姓名、研究方向、进展内容...">
            <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
          </div>
        </div>
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div class="flex flex-wrap gap-2">
            <button @click="teamFilter = 'all'" :class="filterBtnClassTeacher('all')">全部成员</button>
            <button @click="teamFilter = 'doctoral'" :class="filterBtnClassTeacher('doctoral')">博士</button>
            <button @click="teamFilter = 'master'" :class="filterBtnClassTeacher('master')">硕士</button>
            <button @click="teamFilter = 'undergraduate'" :class="filterBtnClassTeacher('undergraduate')">本科</button>
            <button @click="teamFilter = 'normal'" :class="filterBtnClassTeacher('normal')">进度正常</button>
            <button @click="teamFilter = 'warning'" :class="filterBtnClassTeacher('warning')">进度预警</button>
          </div>
          <button @click="openBatchModal" class="bg-secondary text-white px-4 py-2 rounded-lg hover:bg-secondary/90 flex items-center gap-2 transition-colors">
            <i class="fa fa-cog"></i><span>批量设置周期</span>
          </button>
        </div>
      </div>

      <!-- 学生研究进展表格 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="p-6 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-800">学生研究进展</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 text-left text-sm text-gray-500">
              <tr>
                <th class="px-6 py-4 font-medium">学生</th>
                <th class="px-6 py-4 font-medium">研究方向</th>
                <th class="px-6 py-4 font-medium">最新进展</th>
                <th class="px-6 py-4 font-medium">状态</th>
                <th class="px-6 py-4 font-medium">最后更新</th>
                <th class="px-6 py-4 font-medium">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 text-sm">
              <tr v-for="item in filteredTeamList" :key="item.user_id">
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <img :src="getAvatarUrl(item.avatar, item.username)" class="w-8 h-8 rounded-full object-cover">
                    <span>{{ item.username }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-gray-600">{{ item.research_direction || '-' }}</td>
                <td class="px-6 py-4 text-gray-600 max-w-xs truncate">{{ item.weekly_progress || '-' }}</td>
                <td class="px-6 py-4">
                  <span :class="statusBadgeClass(item.computed_status || item.status || 'normal')">{{ statusText(item.computed_status || item.status || 'normal') }}</span>
                </td>
                <td class="px-6 py-4 text-gray-500">{{ formatDate(item.submission_date) }}</td>
                <td class="px-6 py-4">
                  <div v-if="item.progress_id" class="flex gap-2">
                    <button @click="viewDetail(item.progress_id)" class="w-8 h-8 bg-primary/10 text-primary rounded-lg hover:bg-primary hover:text-white transition-all flex items-center justify-center" title="查看详情">
                      <i class="fa fa-eye"></i>
                    </button>
                    <button @click="viewDetail(item.progress_id)" class="w-8 h-8 bg-green-100 text-green-600 rounded-lg hover:bg-green-500 hover:text-white transition-all flex items-center justify-center" title="沟通">
                      <i class="fa fa-comment"></i>
                    </button>
                  </div>
                  <span v-else class="text-gray-400 text-sm">暂无进展</span>
                </td>
              </tr>
              <tr v-if="filteredTeamList.length === 0">
                <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                  <i class="fa fa-inbox text-4xl mb-4"></i>
                  <p>暂无学生进展数据</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- 分页 -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="flex items-center gap-2">
                <label class="text-sm text-gray-600">每页显示</label>
                <select v-model="teamPerPage" @change="fetchTeamProgress()" class="px-3 py-1 border border-gray-300 rounded-lg text-sm">
                  <option value="10">10条</option>
                  <option value="20">20条</option>
                  <option value="50">50条</option>
                </select>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button @click="teamCurrentPage--; fetchTeamProgress()" :disabled="teamCurrentPage === 1" class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50">
                <i class="fa fa-chevron-left mr-1"></i>上一页
              </button>
              <span class="px-3 py-1 text-sm text-gray-600">第 {{ teamCurrentPage }} 页</span>
              <button @click="teamCurrentPage++; fetchTeamProgress()" :disabled="teamCurrentPage >= teamTotalPages" class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50">
                下一页<i class="fa fa-chevron-right ml-1"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 提交/编辑进展弹窗 -->
    <SubmitModal
      v-model="showSubmitModal"
      :editing-id="editingId"
      :research-direction="userStore.researchDirection"
      :existing-attachments="existingAttachments"
      :initial-data="editingData"
      @submit="handleSubmit"
      @close="closeSubmitModal"
    />

    <!-- 详情弹窗 -->
    <ProgressDetailModal
      v-model="showDetailModal"
      :progress-data="detailData"
      :is-teacher="userStore.role !== 'student'"
      @send-feedback="handleSendFeedback"
    />

    <!-- 批量设置弹窗 -->
    <BatchSettingsModal
      v-model="showBatchModal"
      :student-list="teamList"
      @submit="handleBatchSet"
    />

    <!-- Toast -->
    <div v-if="toast.show" :class="toastClass" class="fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg z-50 transition-all">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import * as api from '../api/research_progress'
import { getAvatarUrl } from '../config'
import SubmitModal from '../components/SubmitModal.vue'
import ProgressDetailModal from '../components/ProgressDetailModal.vue'
import BatchSettingsModal from '../components/BatchSettingsModal.vue'

const userStore = useUserStore()

// 学生视图状态
const activeTab = ref('my')
const mySettings = ref(null)
const myProgressList = ref([])
const mySearchKeyword = ref('')
const myCurrentPage = ref(1)
const myPerPage = ref(10)
const latestProgress = ref(null)

// 学生端团队进展
const studentTeamList = ref([])
const studentTeamStats = ref({})
const studentFilter = ref('all')
const studentSearchKeyword = ref('')
const studentCurrentPage = ref(1)
const studentPerPage = ref(10)
const studentTotalPages = ref(1)

// 导师/管理员视图状态
const teamStats = ref({})
const teamList = ref([])
const teamFilter = ref('all')
const teamSearchKeyword = ref('')
const teamCurrentPage = ref(1)
const teamPerPage = ref(10)
const teamTotalPages = ref(1)

// 弹窗状态
const showSubmitModal = ref(false)
const showDetailModal = ref(false)
const showBatchModal = ref(false)
const editingId = ref(null)
const editingData = ref(null)
const existingAttachments = ref([])
const detailData = ref(null)

// Toast
const toast = ref({ show: false, message: '', type: 'success' })

// 计算属性
const filteredHistory = computed(() => {
  const list = myProgressList.value.filter(item => item.id !== latestProgress.value?.id)
  if (!mySearchKeyword.value) return list
  const term = mySearchKeyword.value.toLowerCase()
  return list.filter(item =>
    (item.research_direction?.toLowerCase().includes(term)) ||
    (item.weekly_progress?.toLowerCase().includes(term))
  )
})

const myTotalPages = computed(() => Math.ceil(filteredHistory.value.length / myPerPage.value) || 1)

const paginatedHistory = computed(() => {
  const start = (myCurrentPage.value - 1) * myPerPage.value
  return filteredHistory.value.slice(start, start + myPerPage.value)
})

// 学生端团队进展本地过滤
const filteredStudentTeamList = computed(() => {
  if (!studentSearchKeyword.value) return studentTeamList.value
  const term = studentSearchKeyword.value.toLowerCase()
  return studentTeamList.value.filter(item =>
    (item.username?.toLowerCase().includes(term)) ||
    (item.research_direction?.toLowerCase().includes(term)) ||
    (item.user_research_direction?.toLowerCase().includes(term)) ||
    (item.degree_type?.toLowerCase().includes(term)) ||
    (item.weekly_progress?.toLowerCase().includes(term)) ||
    (item.next_goal?.toLowerCase().includes(term))
  )
})

// 导师端团队进展本地过滤
const filteredTeamList = computed(() => {
  if (!teamSearchKeyword.value) return teamList.value
  const term = teamSearchKeyword.value.toLowerCase()
  return teamList.value.filter(item =>
    (item.username?.toLowerCase().includes(term)) ||
    (item.research_direction?.toLowerCase().includes(term)) ||
    (item.user_research_direction?.toLowerCase().includes(term)) ||
    (item.degree_type?.toLowerCase().includes(term)) ||
    (item.weekly_progress?.toLowerCase().includes(term)) ||
    (item.next_goal?.toLowerCase().includes(term))
  )
})

// 样式计算
const tabClass = (tab) => tab === activeTab.value
  ? 'px-4 py-2 bg-primary text-white rounded-lg font-medium transition-colors'
  : 'px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors'

const filterBtnClass = (filter) => studentFilter.value === filter
  ? 'px-3 py-1 bg-primary/10 text-primary text-sm rounded-lg'
  : 'px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-lg hover:bg-gray-200'

const filterBtnClassTeacher = (filter) => teamFilter.value === filter
  ? 'px-3 py-1 bg-primary/10 text-primary text-sm rounded-lg'
  : 'px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-lg hover:bg-gray-200'

const statusBadgeClass = (status) => {
  const map = {
    normal: 'text-green-600 bg-green-100 px-2 py-1 rounded-full text-xs',
    delayed: 'text-yellow-600 bg-yellow-100 px-2 py-1 rounded-full text-xs',
    warning: 'text-yellow-600 bg-yellow-100 px-2 py-1 rounded-full text-xs',
    not_updated: 'text-gray-600 bg-gray-100 px-2 py-1 rounded-full text-xs'
  }
  return map[status] || map.normal
}

const statusText = (status) => {
  const map = { normal: '进度正常', delayed: '进度预警', warning: '进度预警', not_updated: '未更新' }
  return map[status] || '进度正常'
}

const periodText = (period) => {
  const map = { weekly: '每周提交', biweekly: '每两周提交', monthly: '每月提交' }
  return map[period] || '每周提交'
}

const toastClass = computed(() => toast.value.type === 'error' ? 'bg-red-500 text-white' : toast.value.type === 'info' ? 'bg-blue-500 text-white' : 'bg-green-500 text-white')

// 方法
const formatDate = (dateStr) => {
  if (!dateStr) return '--'
  // 处理时间字符串，确保显示北京时间
  const date = new Date(dateStr)
  const options = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'Asia/Shanghai'
  }
  return new Intl.DateTimeFormat('zh-CN', options).format(date)
}

const getAvatarUrl2 = (item) => getAvatarUrl(item.avatar, item.username)

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3000)
}

// 标签切换
const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'team') {
    fetchStudentTeamProgress()
    fetchStudentTeamStats()
  }
}

// 学生端方法
const fetchMyProgress = async () => {
  try {
    const res = await api.getMyProgress()
    if (res.data.success) {
      myProgressList.value = res.data.data?.items || res.data.data || []
      if (myProgressList.value.length > 0) {
        latestProgress.value = myProgressList.value[0]
      }
    }
  } catch (e) {
    console.error('获取我的进展失败:', e)
  }
}

const fetchMySettings = async () => {
  try {
    const res = await api.getMySettings()
    if (res.data.success) {
      mySettings.value = res.data.data
    }
  } catch (e) {
    console.error('获取我的设置失败:', e)
  }
}

const fetchStudentTeamProgress = async () => {
  try {
    const params = { page: studentCurrentPage.value, limit: studentPerPage.value }
    if (studentFilter.value === 'doctoral' || studentFilter.value === 'master' || studentFilter.value === 'undergraduate') {
      params.student_type = studentFilter.value
    } else if (studentFilter.value === 'normal') {
      params.status = 'normal'
    } else if (studentFilter.value === 'warning') {
      params.status = 'warning'
    }
    const res = await api.getTeamProgress(params)
    if (res.data.success) {
      studentTeamList.value = res.data.data || []
      studentTotalPages.value = res.data.pagination?.total_pages || 1
    }
  } catch (e) {
    console.error('获取团队进展失败:', e)
  }
}

const fetchStudentTeamStats = async () => {
  try {
    const res = await api.getTeamStats()
    if (res.data.success) {
      studentTeamStats.value = res.data.data || {}
    }
  } catch (e) {
    console.error('获取团队统计失败:', e)
  }
}

// 导师端方法
const fetchTeamStats = async () => {
  try {
    const res = await api.getTeamStats()
    if (res.data.success) {
      teamStats.value = res.data.data || {}
    }
  } catch (e) {
    console.error('获取团队统计失败:', e)
  }
}

const fetchTeamProgress = async () => {
  try {
    const params = { page: teamCurrentPage.value, limit: teamPerPage.value }
    if (teamFilter.value === 'doctoral' || teamFilter.value === 'master' || teamFilter.value === 'undergraduate') {
      params.student_type = teamFilter.value
    } else if (teamFilter.value === 'normal') {
      params.status = 'normal'
    } else if (teamFilter.value === 'warning') {
      params.status = 'warning'
    }
    const res = await api.getTeamProgress(params)
    if (res.data.success) {
      teamList.value = res.data.data || []
      teamTotalPages.value = res.data.pagination?.total_pages || 1
    }
  } catch (e) {
    console.error('获取团队进展失败:', e)
  }
}

// 弹窗方法
const openSubmitModal = () => {
  editingId.value = null
  editingData.value = null
  existingAttachments.value = []
  showSubmitModal.value = true
}

const closeSubmitModal = () => {
  showSubmitModal.value = false
  editingId.value = null
  editingData.value = null
  existingAttachments.value = []
}

const editProgress = async (id) => {
  try {
    const res = await api.getProgressDetail(id)
    if (res.data.success) {
      editingId.value = id
      editingData.value = res.data.data
      existingAttachments.value = res.data.data.attachments || []
      showSubmitModal.value = true
    } else {
      showToast(res.data.message || '获取详情失败', 'error')
    }
  } catch (e) {
    const message = e.response?.data?.message || '网络错误，请稍后重试'
    showToast(message, 'error')
  }
}

const viewDetail = async (id) => {
  try {
    const res = await api.getProgressDetail(id)
    if (res.data.success) {
      detailData.value = res.data.data
      showDetailModal.value = true
    } else {
      showToast(res.data.message || '获取详情失败', 'error')
    }
  } catch (e) {
    const message = e.response?.data?.message || '网络错误，请稍后重试'
    showToast(message, 'error')
  }
}

const openBatchModal = () => {
  showBatchModal.value = true
}

const handleSubmit = async (formData) => {
  try {
    if (editingId.value) {
      await api.updateProgress(editingId.value, formData)
      showToast('更新成功')
    } else {
      await api.submitProgress(formData)
      showToast('提交成功')
    }
    closeSubmitModal()
    fetchMyProgress()
  } catch (e) {
    showToast('提交失败', 'error')
  }
}

const handleSendFeedback = async (feedback) => {
  try {
    await api.sendFeedback(detailData.value.id, feedback)
    showToast('反馈发送成功')
    showDetailModal.value = false
    fetchTeamProgress()
  } catch (e) {
    showToast('发送失败', 'error')
  }
}

const handleBatchSet = async (data) => {
  try {
    await api.batchSetSettings(data)
    showToast('批量设置成功')
    showBatchModal.value = false
    fetchTeamProgress()
  } catch (e) {
    showToast('设置失败', 'error')
  }
}

// 监听筛选变化
watch(studentFilter, () => {
  studentCurrentPage.value = 1
  fetchStudentTeamProgress()
})

watch(teamFilter, () => {
  teamCurrentPage.value = 1
  fetchTeamProgress()
})

// 初始化
onMounted(() => {
  if (userStore.role === 'student') {
    fetchMyProgress()
    fetchMySettings()
  } else {
    fetchTeamStats()
    fetchTeamProgress()
  }
})
</script>

<style scoped>
.progress-item {
  background: white;
  border-radius: 0.75rem;
  border: 1px solid #f3f4f6;
  padding: 1rem;
  margin-bottom: 1rem;
  transition: all 0.2s;
}
.progress-item:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
</style>