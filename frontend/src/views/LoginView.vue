<template>
  <!-- 竞品 1:1 登录页：全屏分屏（左 flex-1 渐变展示 + 右 500px 白底表单） -->
  <div class="login-container">
    <!-- 左侧展示区域（竞品：linear-gradient 135deg #667eea→#764ba2 + 浮动圆形装饰） -->
    <div class="showcase-section">
      <div class="showcase-content">
        <!-- 品牌区（竞品：60px logo 圆角方块 + 42px 标题 + 18px 副标题） -->
        <div class="brand-header">
          <div class="logo-wrapper">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-white">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h1 class="brand-title">AI 测试编排平台</h1>
          </div>
          <p class="brand-subtitle">智能体工作流 · 质量资产 · 平台运维</p>
        </div>

        <!-- 2×2 特性展示（竞品：玻璃拟态 feature-card，渐变 icon） -->
        <div class="features-grid">
          <div class="feature-card" v-for="f in features" :key="f.title">
            <div class="feature-icon" :style="{ background: f.color }">
              <span class="feature-icon-emoji">{{ f.icon }}</span>
            </div>
            <div class="feature-content">
              <h3>{{ f.title }}</h3>
              <p>{{ f.desc }}</p>
            </div>
          </div>
        </div>

        <!-- AI 能力徽章（竞品：capability-badge 胶囊形） -->
        <div class="ai-capabilities">
          <div class="capability-badge" v-for="b in badges" :key="b">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4">
              <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ b }}</span>
          </div>
        </div>
      </div>

      <!-- 浮动装饰形状（竞品：4 个半透明圆形 + float 动画） -->
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
      </div>
    </div>

    <!-- 右侧登录表单（竞品：500px 白底 + 400px 表单容器） -->
    <div class="login-section">
      <div class="login-form-wrapper">
        <div class="form-header">
          <h2>欢迎登录</h2>
          <p>AI 测试编排平台 · 测试负责人入口</p>
        </div>

        <!-- 登录模式切换（竞品：mode-tabs 胶囊切换） -->
        <div class="mode-tabs">
          <button type="button" class="mode-tab" :class="{ active: loginMode === 'password' }" @click="loginMode = 'password'">
            密码登录
          </button>
          <button type="button" class="mode-tab" :class="{ active: loginMode === 'sms' }" @click="loginMode = 'sms'">
            短信登录
          </button>
        </div>

        <form @submit.prevent="onLogin" class="login-form">
          <!-- 密码登录 -->
          <template v-if="loginMode === 'password'">
            <div class="form-group">
              <input v-model="form.name" class="login-input" placeholder="测试负责人" autocomplete="username" />
            </div>
            <div class="form-group">
              <input v-model="form.password" type="password" class="login-input" placeholder="密码" autocomplete="current-password" @keyup.enter="onLogin" />
            </div>
          </template>

          <!-- 短信登录（mock，无后端） -->
          <template v-else>
            <div class="form-group">
              <input v-model="form.phone" class="login-input" placeholder="手机号" maxlength="11" />
            </div>
            <div class="form-group">
              <input v-model="form.smsCode" class="login-input" placeholder="短信验证码" maxlength="6" />
            </div>
          </template>

          <button type="submit" :disabled="loading" class="login-button">
            {{ loading ? '登录中…' : '登 录' }}
          </button>
        </form>

        <div class="form-footer">
          <p class="text-[12px] text-gray-300 mt-8">登录即代表同意平台审计与合规策略（密钥不明文落盘）</p>
        </div>
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

const loginMode = ref('password')
const form = reactive({ name: '测试负责人', password: '', phone: '', smsCode: '' })
const loading = ref(false)

const features = [
  { icon: '🧩', title: '智能编排', desc: 'PRD §8 五大编排范式，节点级确定性门禁', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { icon: '🧠', title: 'Agnes 模型', desc: 'Agnes 3.0 Flash 高速推理，128K 上下文', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { icon: '🏅', title: '认证资产', desc: '用例/脚本/数据模板质量门槛 + 版本锁定', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { icon: '🔒', title: '审计账本', desc: '哈希链不可篡改，证据可追溯', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
]

const badges = ['AI 用例生成', '智能测试', '多端执行', '定时任务']

async function onLogin() {
  if (loginMode.value === 'password' && !form.name.trim()) return
  loading.value = true
  try {
    await auth.login(form.name.trim() || '测试负责人', form.password)
  } finally {
    loading.value = false
  }
  router.replace('/dashboard')
}
</script>

<style scoped>
/* ===== 竞品 1:1 登录页（testhub_platform-main Login.vue 复刻） ===== */
.login-container {
  height: 100vh;
  display: flex;
  background: #f5f7fa;
  overflow: hidden;
}

/* 左侧展示区域 */
.showcase-section {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 60px;
}

.showcase-content {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 600px;
  color: white;
}

.brand-header {
  margin-bottom: 60px;
  animation: fadeInDown 0.8s ease-out;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.brand-title {
  font-size: 42px;
  font-weight: 700;
  margin: 0;
  color: white;
  letter-spacing: -1px;
}

.brand-subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin: 0;
  font-weight: 300;
  letter-spacing: 1px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 60px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  animation: fadeInUp 0.8s ease-out;
}

.feature-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.feature-icon-emoji {
  font-size: 24px;
  line-height: 1;
}

.feature-content h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: white;
}

.feature-content p {
  font-size: 13px;
  margin: 0;
  opacity: 0.8;
  line-height: 1.5;
}

.ai-capabilities {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  animation: fadeInUp 1s ease-out;
}

.capability-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  padding: 10px 20px;
  border-radius: 50px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 14px;
  font-weight: 500;
}

/* 浮动装饰形状 */
.floating-shapes {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  z-index: 1;
  pointer-events: none;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite;
}

.shape-1 { width: 300px; height: 300px; top: -100px; left: -100px; animation-delay: 0s; }
.shape-2 { width: 200px; height: 200px; bottom: -50px; right: -50px; animation-delay: 5s; }
.shape-3 { width: 150px; height: 150px; top: 50%; right: 20%; animation-delay: 10s; }
.shape-4 { width: 100px; height: 100px; bottom: 30%; left: 30%; animation-delay: 15s; }

/* 右侧登录表单 */
.login-section {
  width: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  padding: 60px;
  position: relative;
}

.login-form-wrapper {
  width: 100%;
  max-width: 400px;
}

.form-header {
  text-align: center;
  margin-bottom: 24px;
  animation: fadeIn 0.8s ease-out;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 12px 0;
}

.form-header p {
  font-size: 14px;
  color: #909399;
  margin: 0;
  line-height: 1.6;
}

.mode-tabs {
  display: flex;
  background: #f0f2f5;
  border-radius: 8px;
  padding: 4px;
  margin-bottom: 24px;
}

.mode-tab {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  transition: all 0.3s ease;
  background: transparent;
}

.mode-tab.active {
  background: white;
  color: #667eea;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.mode-tab:hover:not(.active) {
  color: #606266;
}

.login-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 24px;
}

.login-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  outline: none;
  transition: all 0.3s ease;
  background: white;
  box-sizing: border-box;
}

.login-input:hover {
  border-color: #c0c4cc;
}

.login-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.15);
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.login-button:active {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式（竞品：≤1200px 单列，≤768px 纵向堆叠） */
@media (max-width: 1200px) {
  .showcase-section { padding: 40px; }
  .features-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .login-container { flex-direction: column; }
  .showcase-section { min-height: 50vh; padding: 30px; }
  .brand-header { margin-bottom: 30px; }
  .logo-wrapper .brand-title { font-size: 32px; }
  .features-grid { display: none; }
  .login-section { width: 100%; padding: 30px; }
}

/* 动画 */
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(30px, -30px) rotate(90deg); }
  50% { transform: translate(-20px, 20px) rotate(180deg); }
  75% { transform: translate(20px, 10px) rotate(270deg); }
}
</style>
