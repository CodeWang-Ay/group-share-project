// 前端配置文件
// 从环境变量读取后端地址，避免硬编码

// 后端 API 基础地址
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8088'

// 后端服务器地址（用于静态资源如 avatar）
export const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8088'

// 获取完整的 avatar URL
export const getAvatarUrl = (avatar, fallbackName = 'User') => {
  if (!avatar) {
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(fallbackName)}&background=2563eb&color=fff&size=128`
  }
  if (avatar.startsWith('/uploads')) {
    return `${SERVER_URL}${avatar}`
  }
  return avatar
}

// 获取登录页面 URL
export const getLoginUrl = () => `${SERVER_URL}/login`