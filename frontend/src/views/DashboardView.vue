<template>
  <!-- 竞品首页导航：独立全屏渐变背景 + 居中 1200px 卡片网格（meta.noLayout） -->
  <div class="home-page">
    <div class="home-content">
      <!-- 标题区（竞品：3.5rem 主标题 + 1.5rem 副标题） -->
      <div class="home-header">
        <h1 class="home-title">AI 测试编排平台</h1>
        <p class="home-subtitle">选择模块快速进入工作区 · 智能体工作流 / 质量资产 / 平台运维</p>
      </div>

      <!-- 10 模块导航卡（竞品：auto-fit minmax(250px,1fr) gap 30px，80px 圆形 icon） -->
      <div class="nav-grid">
        <div
          v-for="card in navCards"
          :key="card.path"
          class="nav-card polaroid-card"
          @click="goTo(card.path)"
        >
          <div class="nav-icon" :style="{ background: card.color }">
            <span class="nav-icon-emoji">{{ card.icon }}</span>
          </div>
          <h3 class="nav-card-title">{{ card.title }}</h3>
          <p class="nav-card-desc">{{ card.desc }}</p>
          <div class="nav-card-arrow">进入 →</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const navCards = [
  { path: '/workflows', title: '工作流列表', desc: '浏览、搜索与管理全部编排工作流', icon: '📋', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { path: '/editor', title: '编排画布', desc: '拖拽式节点编排，实时预览与调试', icon: '✎', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { path: '/runs', title: '执行追踪', desc: '查看运行状态、日志与门禁结果', icon: '▶', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { path: '/assets', title: '认证资产库', desc: '用例 / 脚本 / 数据模板质量认证与版本锁定', icon: '🏅', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
  { path: '/tasks', title: '异步任务', desc: '长耗时任务调度、重试与结果回收', icon: '⏳', color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
  { path: '/models', title: '模型与额度', desc: 'Agnes 3.0 Flash 配置、Token 额度与用量', icon: '🧠', color: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)' },
  { path: '/audit', title: '审计账本', desc: '哈希链不可篡改操作日志与证据追溯', icon: '🔒', color: 'linear-gradient(135deg, #667eea 0%, #4facfe 100%)' },
  { path: '/capabilities', title: '开放能力', desc: '外部智能体接入审批与 API 网关', icon: '🌐', color: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' },
  { path: '/resources', title: '资源与锁', desc: '设备 / 环境资源池与互斥锁管理', icon: '🗄️', color: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)' },
  { path: '/settings', title: '配置中心', desc: '平台参数、预算阈值与合规策略', icon: '⚙️', color: 'linear-gradient(135deg, #c471f5 0%, #f7797b 100%)' },
]

function goTo(path) {
  router.push(path)
}
</script>

<style scoped>
/* ===== 竞品首页导航（testhub_platform-main Home.vue 复刻） ===== */
.home-page {
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px 20px;
  overflow: hidden;
}

.home-content {
  width: 100%;
  max-width: 1200px;
  max-height: calc(100vh - 60px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4px 8px;
  margin: -4px -8px;
}

/* 标题区 */
.home-header {
  text-align: center;
  margin-bottom: 48px;
}

.home-title {
  font-size: 3.5rem;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 12px 0;
  letter-spacing: -1px;
}

.home-subtitle {
  font-size: 1.5rem;
  color: #6b7280;
  margin: 0;
  font-weight: 300;
}

/* 导航卡网格 */
.nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
}

/* 单张导航卡（保留 .polaroid-card 类名供 Playwright 选择器兼容） */
.nav-card {
  background: white;
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.nav-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
}

.nav-card:hover .nav-icon {
  transform: scale(1.1);
}

/* 80px 圆形彩色 icon */
.nav-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  transition: transform 0.3s ease;
}

.nav-icon-emoji {
  font-size: 36px;
  line-height: 1;
}

/* 卡片文字 */
.nav-card-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 8px 0;
}

.nav-card-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
  min-height: 40px;
}

.nav-card-arrow {
  font-size: 13px;
  color: #667eea;
  font-weight: 600;
  margin-top: 16px;
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.3s ease;
}

.nav-card:hover .nav-card-arrow {
  opacity: 1;
  transform: translateY(0);
}

/* 响应式 */
@media (max-width: 768px) {
  .home-title { font-size: 2.2rem; }
  .home-subtitle { font-size: 1rem; }
  .nav-grid { gap: 16px; }
  .nav-card { padding: 24px 16px; }
  .nav-icon { width: 60px; height: 60px; }
  .nav-icon-emoji { font-size: 28px; }
}
</style>
