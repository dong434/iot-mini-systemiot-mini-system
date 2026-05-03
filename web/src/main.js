// createApp用于创建数据
import { createApp } from 'vue'
// 引入根组件
import App from './App.vue'
import Particles from "vue3-particles"
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
//引入路由器
import router from './router'

// 🌟 1. 新增：引入完整的粒子引擎包
import { loadFull } from "tsparticles"

// 🌟 2. 新增：引擎初始化点火函数
const particlesInit = async (engine) => {
    await loadFull(engine);
};

const app=createApp(App)
app.use(Particles)
app.use(ElementPlus)
app.use(router)
app.mount('#app')
