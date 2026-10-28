/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 竞品视觉规格（testhub_platform-main 对齐）：深蓝侧栏 + 蓝主色 + 灰主区
        competitor: {
          navy: '#001529',        // 侧栏背景
          primary: '#1890ff',     // 主色 / 激活 / 链接
          'primary-dark': '#096dd9',
          main: '#f5f5f5',        // 主区背景
          text: '#303133',        // 正文
          'text-2': '#909399',   // 次要文本
          border: '#e8e8e8',     // 描边
          success: '#67c23a',
          warning: '#e6a23c',
          danger: '#f56c6c',
        },
        // polaroid-warm 保留为回退色板
        'polaroid-warm': {
          50: '#fffdfa',
          100: '#fef9f2',
          200: '#fbeee0',
          300: '#f7dbca',
          400: '#f2c8b1',
          500: '#e9b49a',
          600: '#d69a81',
          700: '#b57b65',
          800: '#945c4a',
          900: '#733d31',
        },
        'warm-accent': '#fdf6e3',
      },
    },
  },
  plugins: [],
}
