import { defineStore } from 'pinia'

const STORAGE_KEY = 'aio_auth'

function readStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch (e) {
    return null
  }
}

// 前端 mock 登录（无后端 /auth 接口）：以 localStorage 持久化"已登录"态
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: readStorage() || null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.user,
    displayName: (state) => (state.user ? state.user.name : ''),
  },
  actions: {
    login(name, password) {
      const user = {
        name: name || '雪 樱',
        role: '测试负责人',
        avatar: (name || '雪 樱').trim().slice(0, 1) || '雪',
        lastLoginAt: new Date().toLocaleString('zh-CN', { hour12: false }),
      }
      this.user = user
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
      } catch (e) {
        /* localStorage 不可用时仅保留内存态 */
      }
      return user
    },
    logout() {
      this.user = null
      try {
        localStorage.removeItem(STORAGE_KEY)
      } catch (e) {
        /* ignore */
      }
    },
  },
})
