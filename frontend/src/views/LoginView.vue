<template>
  <!-- 竞品对齐登录页：左右分屏（无侧栏壳）。左品牌/能力展示 + 右登录表单卡片 -->
  <div class="min-h-screen flex bg-competitor-main">
    <!-- 左侧品牌展示面板（竞品 Login 范式） -->
    <div class="hidden lg:flex flex-1 relative overflow-hidden bg-competitor-navy text-white flex-col justify-between p-10">
      <!-- 装饰形状（竞品：右下角圆形/方块半透明装饰） -->
      <div class="absolute -bottom-24 -right-24 w-96 h-96 rounded-full bg-competitor-primary/20"></div>
      <div class="absolute top-20 right-32 w-24 h-24 rounded-lg bg-white/5 rotate-12"></div>

      <div class="relative z-10">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 bg-competitor-primary rounded-lg flex items-center justify-center text-white text-xl font-bold shadow-lg">AI</div>
          <div class="leading-tight">
            <div class="text-lg font-bold">AI 测试编排平台</div>
            <div class="text-xs text-white/50">智能体工作流 · 质量资产 · 平台运维</div>
          </div>
        </div>
        <h1 class="mt-10 text-3xl font-bold leading-snug">
          一条流水线打通<br />测试分析与执行闭环
        </h1>
        <p class="mt-4 text-sm text-white/60 max-w-md">
          需求解析 → 用例生成 → 多端执行 → 质量门禁 → 缺陷归档，全流程可观测、可审计、可熔断。
        </p>
      </div>

      <!-- 能力徽章（竞品：capability badges） -->
      <div class="relative z-10 grid grid-cols-2 gap-3 max-w-md">
        <div class="feature-card" v-for="f in features" :key="f.title">
          <div class="text-2xl mb-2">{{ f.icon }}</div>
          <div class="text-sm font-bold">{{ f.title }}</div>
          <div class="text-[11px] text-white/50 mt-1">{{ f.desc }}</div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单卡片 -->
    <div class="w-full lg:w-[480px] flex items-center justify-center p-6 lg:p-10">
      <div class="card-container w-full max-w-sm">
        <div class="text-center mb-6">
          <div class="text-2xl font-bold text-competitor-text">欢迎登录</div>
          <p class="text-xs text-competitor-text-2 mt-1">AI 测试编排平台 · 测试负责人入口</p>
        </div>

        <form @submit.prevent="onLogin" class="space-y-4">
          <div>
            <label class="block text-xs font-medium text-competitor-text-2 mb-1">账号</label>
            <input
              v-model="form.name"
              class="login-input"
              placeholder="测试负责人"
              autocomplete="username"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-competitor-text-2 mb-1">密码</label>
            <input
              v-model="form.password"
              type="password"
              class="login-input"
              placeholder="••••••••"
              autocomplete="current-password"
            />
          </div>

          <div class="flex items-center justify-between text-xs">
            <label class="flex items-center gap-2 text-competitor-text-2 cursor-pointer">
              <input type="checkbox" v-model="form.remember" class="rounded text-competitor-primary" />
              记住我
            </label>
            <span class="text-competitor-text-2">忘记密码？</span>
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 bg-competitor-primary text-white text-sm font-medium rounded-lg hover:bg-competitor-primary-dark transition-colors disabled:opacity-60"
          >
            {{ loading ? '登录中…' : '登 录' }}
          </button>
        </form>

        <p class="text-center text-[11px] text-competitor-text-2 mt-6">
          登录即代表同意平台审计与合规策略（密钥不明文落盘）
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({ name: '测试负责人', password: '', remember: true })
const loading = ref(false)

const features = [
  { icon: '🧩', title: '智能编排', desc: 'PRD §8 五大编排范式，节点级确定性门禁' },
  { icon: '🧠', title: 'Agnes 模型', desc: 'Agnes 3.0 Flash 高速推理，128K 上下文' },
  { icon: '🏅', title: '认证资产', desc: '用例/脚本/数据模板质量门槛 + 版本锁定' },
  { icon: '🔒', title: '审计账本', desc: '哈希链不可篡改，证据可追溯' },
]

async function onLogin() {
  if (!form.name.trim()) return
  loading.value = true
  try {
    await auth.login(form.name.trim(), form.password)
  } finally {
    loading.value = false
  }
  router.replace('/dashboard')
}
</script>

<style scoped>
.feature-card {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 16px;
}
.login-input {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  border: 1px solid var(--c-border, #e8e8e8);
  border-radius: 8px;
  outline: none;
  transition: border-color 0.2s;
  background: #fff;
}
.login-input:focus {
  border-color: var(--c-primary, #1890ff);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.15);
}
</style>
