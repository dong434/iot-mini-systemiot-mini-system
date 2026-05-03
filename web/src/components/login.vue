<template>
  <div class="login-container">
    <div class="login-left">
      <div class="presentation-box">

        <div class="css-battery">
          <div class="battery-head"></div>
          <div class="battery-body">
            <div class="charge-level"></div>
            <div class="charge-level-text">98%</div>
          </div>
        </div>
<!-- ===================左侧用户交互=================================-->
        <h1 class="main-title">温控有锂</h1>
        <p class="sub-title">让每一块锂电池都在舒适区运行</p>
        <div class="decorator-line"></div>
        <div class="tech-tags-container">
          <div class="tech-card ai-card">
            <p class="tag-title">AI 智能温控预测</p>
            <p class="tag-desc">LSTM多维特征融合提前3步预判</p>
          </div>
          <div class="tech-card monitor-card">
            <p class="tag-title">实时热场监控</p>
            <p class="tag-desc">mqtt InfluxDB毫秒级响应</p>
          </div>
          <div class="tech-card warning-card">
            <p class="tag-title">多维预警体系</p>
            <p class="tag-desc">软硬双重联动，警报自动急停</p>
          </div>
        </div>


      </div>
    </div>
    <!-- ===================结束左侧户互动==============================-->
    <div class="login-right">
      <div class="login-box">
        <div class="form-header">
          <h2>温控有锂-智能系统</h2>
          <p>Li-Therm</p>
        </div>

        <el-form @submit.prevent="handlelogin">
          <el-form-item>
            <el-input v-model="userdata.username" placeholder="请输入账号" :prefix-icon="User" size="large" class="custom-input" />
          </el-form-item>

          <el-form-item>
            <el-input v-model="userdata.password" type="password" placeholder="请输入系统密码" :prefix-icon="Lock" show-password size="large" class="custom-input" :class="{ 'error-shake': pass === 'no' }" @input="pass = 'null'" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" class="submit-btn" native-type="submit" :loading="loading">
              进入监控中心
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <span>&copy; 2026 温控有锂研发团队</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { User, Lock } from '@element-plus/icons-vue'

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`
const router = useRouter()
const pass = ref("null")
const loading = ref(false)
const userdata = reactive({ username: '', password: '' })

const handlelogin = async () => {
  if (!userdata.username || !userdata.password) {
    ElMessage.warning("账号和密码不能为空！");
    return;
  }
  loading.value = true;
  const formData = new FormData();
  formData.append("username", userdata.username);
  formData.append("password", userdata.password);

  try {
    const response = await fetch(`${API_BASE}/login`, {
      method: "POST",
      body: formData
    });
    const data = await response.json();
    if (data.message === "登录成功") {
      ElMessage.success("验证通过，正在初始化系统...");
      sessionStorage.setItem("token", data.token);
      sessionStorage.setItem("role", data.role);
      setTimeout(() => { router.push("/dashboard"); }, 500);
    } else {
      pass.value = "no"
      ElMessage.error(data.message);
    }
  } catch (error) {
    ElMessage.error("系统连接超时，请检查后端服务！");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* ================= 全局左右布局 ================= */
.login-container {
  height: 100vh;
  display: flex;
  background: #0f172a; /* 极客深蓝底色 */
  overflow: hidden;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

/* ================= 左侧：视觉与动画 ================= */
.login-left {
  flex: 1.2;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  background: radial-gradient(circle at 50% 40%, #1e293b 0%, #0f172a 100%);
  border-right: 1px solid rgba(255,255,255,0.05);
}

.presentation-box {
  text-align: center;
  color: #fff;
  z-index: 2;
}

/* 🌟 核心解读：纯 CSS 电池绘制 */
.css-battery {
  width: 100px;
  margin: 0 auto 30px auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.battery-head {
  width: 30px;
  height: 10px;
  background: #475569;
  border-radius: 4px 4px 0 0;
}

.battery-body {
  width: 80px;
  height: 160px;
  border: 4px solid #475569;
  border-radius: 12px;
  position: relative; /* 定位锚点 */
  overflow: hidden;   /* 让超出的绿色液体隐藏 */
  background: rgba(0,0,0,0.2);
  display: flex;
  justify-content: center;
  align-items: center;
}

.charge-level-text {
  position: absolute;
  color: #fff;
  font-weight: bold;
  font-size: 20px;
  z-index: 10;
  text-shadow: 0 2px 4px rgba(0,0,0,0.8);
}

/* 🌟 核心解读：充电液位动画 */
.charge-level {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(0deg, #10b981 0%, #34d399 100%);
  animation: charging 4s ease-in-out infinite; /* 无限循环充电动画 */
}

@keyframes charging {
  0%   { height: 10%; filter: hue-rotate(40deg); } /* 没电时偏红/黄 */
  50%  { height: 98%; filter: hue-rotate(0deg); }  /* 满电时纯绿 */
  100% { height: 10%; filter: hue-rotate(40deg); }
}

/* 文字与装饰 */
.main-title {
  font-size: 3.5rem;
  font-weight: 900;
  background: linear-gradient(120deg, #10b981, #0ea5e9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  letter-spacing: 2px;
}

.sub-title {
  color: #94a3b8;
  letter-spacing: 4px;
  margin-top: 10px;
}

.decorator-line {
  width: 80px;
  height: 3px;
  background: #10b981;
  margin: 25px auto;
  border-radius: 2px;
  box-shadow: 0 0 10px rgba(16,185,129,0.5);
}

.tech-tags-container {
  display: flex;
  flex-direction: row; /* 横向排列 */
  justify-content: center;
  gap: 15px;
  margin-top: 30px;
}

.tech-card {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  text-align: center;
  height: 60px; /* 初始高度 */
  width: 130px; /* 初始宽度 */
  border-radius: 12px;
  color: white;
  cursor: pointer;
  /* 贝塞尔曲线让缩放更带感 */
  transition: 400ms cubic-bezier(0.25, 0.8, 0.25, 1);
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

/* 融入底边发光特效 */
.ai-card { border-bottom: 3px solid #f43f5e; }
.monitor-card { border-bottom: 3px solid #3b82f6; }
.warning-card { border-bottom: 3px solid #22c55e; }

.tag-title {
  font-size: 14px;
  font-weight: 700;
  margin: 0;
  color: #e2e8f0;
  transition: transform 0.3s;
}

/* 默认隐藏精简注释 */
.tag-desc {
  font-size: 11px;
  color: #94a3b8;
  margin: 0;
  padding: 0 8px;
  opacity: 0;
  height: 0;
  transition: all 0.3s;
}

/* 1. 当前卡片悬浮效果：放大、提亮、显示注释 */
.tech-card:hover {
  transform: scale(1.2); /* 放大 1.2 倍 */
  background: rgba(30, 41, 59, 0.95);
  box-shadow: 0 10px 20px rgba(0,0,0,0.5);
  z-index: 10;
  height: 80px; /* 撑开高度容纳注释 */
}

.tech-card:hover .tag-title {
  transform: translateY(-2px);
}

.tech-card:hover .tag-desc {
  opacity: 1;
  height: auto;
  margin-top: 6px;
}

/* 🌟 2. 知识点核心：非悬浮卡片的模糊变暗效果 */
.tech-tags-container:hover > .tech-card:not(:hover) {
  filter: blur(4px); /* 背景模糊 */
  transform: scale(0.9); /* 稍微缩小 */
  opacity: 0.5; /* 降低透明度 */
}

/* ================= 右侧：登录区 ================= */
.login-right {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #0b1120;
}

.login-box {
  width: 360px;
  padding: 40px;
  background: rgba(30, 41, 59, 0.4);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.form-header {
  text-align: center;
  margin-bottom: 35px;
}

.form-header h2 {
  color: #f8fafc;
  margin: 0 0 5px 0;
  font-size: 24px;
  letter-spacing: 1px;
}

.form-header p {
  color: #64748b;
  font-size: 12px;
  letter-spacing: 3px;
  margin: 0;
}

/* 输入框深色覆盖 */
:deep(.el-input__wrapper) {
  background-color: rgba(15, 23, 42, 0.6) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
}
:deep(.el-input__inner) { color: #f1f5f9 !important; }

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: bold;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  margin-top: 10px;
  transition: all 0.3s;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}

/* 错误震动 */
.error-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }
:deep(.error-shake .el-input__wrapper) { box-shadow: 0 0 0 1px #ef4444 inset !important; }

@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}

/* ✨ 底部版权样式 */
.login-footer {
  margin-top: 40px;
  text-align: center;
  border-top: 1px dashed rgba(255,255,255,0.1);
  padding-top: 15px;
}

.login-footer span {
  font-size: 12px;
  color: #64748b;
  letter-spacing: 1px;
}

@media screen and (max-width: 768px) {
  .login-container { flex-direction: column; height: auto; min-height: 100vh; overflow-y: auto; }
  .login-left { padding: 40px 10px; border-right: none; border-bottom: 1px solid rgba(255,255,255,0.05); }
  .tech-tags-container { flex-wrap: wrap; }
  .login-right { padding: 30px 15px; }
  .login-box { width: 100%; padding: 25px 15px; }
  .main-title { font-size: 2.5rem; }
}
</style>
