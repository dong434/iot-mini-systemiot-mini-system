<template>
  <el-container class="layout-container">

    <el-aside class="aside-menu" width="220px">
      <div class="system-title">
        <span class="text">温控有锂</span>
      </div>

      <el-menu :default-active="activeMenu" @select="handleMenuSelect" :default-openeds="['devices']" active-text-color="#10b981" background-color="transparent" text-color="#94a3b8">
        <el-sub-menu index="devices">
          <template #title><el-icon><icon-menu /></el-icon><span>多设备阵列管理</span></template>
          <el-menu-item index="battery1">1号电池组 </el-menu-item>
          <el-menu-item index="battery2">2号电池组 </el-menu-item>
          <el-menu-item index="battery3">3号电池组 </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="history" v-if="userRole === 'admin'">
          <template #title><el-icon><Document /></el-icon><span>历史数据</span></template>
          <el-menu-item index="history_battery1">1号设备历史</el-menu-item>
          <el-menu-item index="history_battery2">2号设备历史</el-menu-item>
          <el-menu-item index="history_battery3">3号设备历史</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="main-header">
        <div class="header-left">
          <h2 class="page-title">数据监控中心 - 当前连接：<span class="text-green">{{ currentDeviceName }}</span>
            <el-tag :type="userRole === 'admin' ? 'danger' : 'success'" effect="dark" round style="margin-left: 15px;">
              {{ userRole === 'admin' ? '运维管理权限' : '普通用户权限' }}
            </el-tag>
          </h2>
        </div>
      </el-header>

      <el-main class="main-content">
        <div v-show="['battery1', 'battery2', 'battery3'].includes(activeMenu)" class="page-channel">

          <div class="kpi-container flex-around">

            <div class="kpi-card glass-panel tech-corner">
              <div class="kpi-header"><span class="blink-dot dot-green"></span> 电量与容量管理</div>
              <div class="kpi-main"><span class="kpi-value text-green">{{ kpi.soc.toFixed(1) }}</span><span class="kpi-unit">% (SOC)</span></div>
              <div class="kpi-sub-list">
                <div class="sub-item"><span>SOH / 续航预估</span><span>{{ kpi.soh }}% / {{ kpi.remain_time }}</span></div>
                <div class="sub-item"><span>总容量 / 已用容量</span><span class="text-light">{{ kpi.total_capacity }}Ah / {{ kpi.used_capacity.toFixed(1) }}Ah</span></div>
              </div>
            </div>

            <div class="kpi-card glass-panel tech-corner">
              <div class="kpi-header"><span class="blink-dot dot-blue"></span> 核心热管理监控</div>
              <div class="kpi-main"><span class="kpi-value text-blue">{{ kpi.current_temp.toFixed(1) }}</span><span class="kpi-unit">℃ (包内均温)</span></div>
              <div class="kpi-sub-list">
                <div class="sub-item"><span>最高温 / 最大温差</span><span class="text-danger">{{ kpi.highest_temp.toFixed(1) }}℃ / {{ kpi.temp_diff.toFixed(1) }}℃</span></div>
                <div class="sub-item"><span>环境温 / 进出风口</span><span class="text-light">{{ kpi.env_temp }}℃ | {{ kpi.inlet_temp }}℃/{{ kpi.outlet_temp }}℃</span></div>
              </div>
            </div>

            <div class="kpi-card glass-panel tech-corner">
              <div class="kpi-header"><span class="blink-dot dot-orange"></span> 电气与均衡系统</div>
              <div class="kpi-main"><span class="kpi-value text-orange">{{ kpi.power }}</span><span class="kpi-unit">kW ({{ kpi.power_direction }})</span></div>
              <div class="kpi-sub-list">
                <div class="sub-item"><span>单体最大压差</span><span :class="kpi.volt_diff > 0.2 ? 'text-danger' : 'text-safe'">{{ kpi.volt_diff.toFixed(3) }} V</span></div>
                <div class="sub-item"><span>电池总压 / 均衡状态</span><span>{{ kpi.total_voltage.toFixed(1) }} V / <b :class="kpi.balance_status === '开启' ? 'text-green' : ''">{{ kpi.balance_status }}</b></span></div>
              </div>
            </div>

            <div class="kpi-card glass-panel tech-corner" :class="{'safe-border': kpi.sys_status === '正常', 'danger-border': kpi.sys_status !== '正常'}">
              <div class="kpi-header"><span class="blink-dot" :class="kpi.sys_status === '正常' ? 'dot-green' : 'dot-red'"></span> 安全故障与外设</div>
              <div class="kpi-main">
                <span class="kpi-value" :class="kpi.sys_status === '正常' ? 'text-safe' : 'text-danger'" style="font-size: 22px;">{{ kpi.sys_status }}</span>
              </div>
              <div class="kpi-sub-list">
                <div class="sub-item">
                  <span>报警指示</span>
                  <span :class="kpi.fault_code === '无报警' ? 'text-safe' : 'text-danger'" style="max-width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {{ kpi.fault_code }}
                  </span>
                </div>
                <div class="sub-item"><span>风扇 / 水泵转速</span><span>{{ kpi.fan_speed }} / {{ kpi.pump_speed }} rpm</span></div>
                <div class="sub-item" style="display: none;"><span>绝缘电阻</span><span>{{ kpi.insulation_res }} MΩ</span></div>
              </div>
            </div>

          </div>

          <div v-if="userRole === 'admin'">
            <div class="middle-matrix">
              <div class="wing-panel">
                <div id="chartLeft1" class="chart-box glass-panel"></div>
                <div id="chartLeft2" class="chart-box glass-panel"></div>
              </div>
              <div class="center-panel">
                <div id="mainChart" class="main-chart-box glass-panel"></div>
              </div>
              <div class="wing-panel">
                <div id="chartRight1" class="chart-box glass-panel"></div>
                <div id="chartRight2" class="chart-box glass-panel"></div>
              </div>
            </div>

            <div class="footer-section flex-between">
              <div class="alarm-box glass-panel">
                <h3>运维面板：报警记录 & 故障记录</h3>
                <div class="alarm-list">
                  <div class="y_alarm" v-for="item in alarm_list" :key="item.time">
                    <span class="alarm_time">{{item.time}}</span>
                    <span class="alarm_msg" :class="{'text-danger': item.msg.includes('紧急')}">{{item.msg}}</span>
                  </div>
                </div>
              </div>

              <div class="control-box glass-panel">
                <el-button @click="() => if_stop_battery('manual')" v-if="if_stop === 'no'" type="danger" size="large" class="control-btn shake-btn">强制关闭设备</el-button>
                <el-button @click="if_start_battery" v-else type="success" size="large" class="control-btn" style="background: #10b981; border: none; box-shadow: 0 8px 15px rgba(16, 185, 129, 0.4);">恢复开启设备</el-button>
              </div>
            </div>
          </div>

        </div>

        <div v-show="activeMenu.startsWith('history_')" class="page-channel glass-panel" style="padding: 20px; height: calc(100vh - 110px); display: flex; flex-direction: column;">

          <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <h2 class="text-blue" style="margin: 0; font-size: 20px;">
              <span class="blink-dot dot-cyan"></span> 历史回溯记录
            </h2>
            <el-radio-group v-model="historyType" size="large" fill="#10b981">
              <el-radio-button label="temp">温度历史</el-radio-button>
              <el-radio-button label="volt">电压历史</el-radio-button>
              <el-radio-button label="curr">电流历史</el-radio-button>
            </el-radio-group>
          </div>

          <div style="flex: 1; overflow: hidden; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <el-table :data="historyData" height="100%" style="width: 100%;" class="dark-table" stripe>
              <el-table-column label="记录时间" width="220" align="center">
                <template #default="scope">
                  <span style="color: #94a3b8; font-weight: bold;">{{ formatTime(scope.row.time) }}</span>
                </template>
              </el-table-column>

              <template v-if="historyType === 'temp'">
                <el-table-column prop="pack_temp" label="包内均温 (℃)" align="center" />
                <el-table-column prop="highest_temp" label="最高单体温 (℃)" align="center">
                  <template #default="scope">
                    <span :class="scope.row.highest_temp > 55 ? 'text-danger' : 'text-safe'">{{ scope.row.highest_temp }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="lowest_temp" label="最低单体温 (℃)" align="center" />
              </template>

              <template v-if="historyType === 'volt'">
                <el-table-column prop="total_voltage" label="总电压 (V)" align="center">
                  <template #default="scope">
                    <span class="text-orange">{{ scope.row.total_voltage }} V</span>
                  </template>
                </el-table-column>
                <el-table-column label="单体监控样本" align="center">
                  <template #default="scope">
                    <span style="color: #94a3b8; font-size: 12px;">{{ scope.row.cell_voltages_str }}</span>
                  </template>
                </el-table-column>
              </template>

              <template v-if="historyType === 'curr'">
                <el-table-column prop="total_current" label="充放电电流 (A)" align="center">
                  <template #default="scope">
                      <span :class="scope.row.total_current < 0 ? 'text-blue' : 'text-green'">
                        {{ scope.row.total_current }} A
                      </span>
                  </template>
                </el-table-column>
                <el-table-column prop="soc" label="当时剩余电量 (SOC)" align="center" />
              </template>
            </el-table>
          </div>

        </div>

<!--        <div v-show="activeMenu === 'settings' && userRole === 'admin'" class="page-channel glass-panel" style="padding: 40px;">-->
<!--          <h2 class="text-orange" style="margin-bottom: 30px;">温控与报警阈值参数下发 (仅运维可见)</h2>-->
<!--          <el-form label-width="150px" style="max-width: 600px; color: white;">-->
<!--            <el-form-item label="单体最高温度熔断线">-->
<!--              <el-slider v-model="thresholdTemp" :min="40" :max="80" show-input />-->
<!--            </el-form-item>-->
<!--            <el-form-item label="单体压差报警线 (V)">-->
<!--              <el-input-number v-model="thresholdDiff" :step="0.1" :min="0.1" :max="1.5" />-->
<!--            </el-form-item>-->
<!--            <el-form-item label="安全急停策略">-->
<!--              <el-switch v-model="aiStrategy" active-text="AI自动接管切断" inactive-text="人工确认切断" />-->
<!--            </el-form-item>-->
<!--            <el-form-item>-->
<!--              <el-button type="success" style="background: #10b981; border: none; font-weight: bold; width: 150px;">下发至底层网关</el-button>-->
<!--            </el-form-item>-->
<!--          </el-form>-->
<!--        </div>-->

      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import * as echarts from 'echarts'
import { ref, onMounted, onUnmounted} from 'vue';
import { ElMessage } from 'element-plus'
import { Menu as IconMenu, Document, Setting } from '@element-plus/icons-vue'

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`
const formatTime = (timeStr) => {
  if (!timeStr) return '';
  const d = new Date(timeStr);
  if (isNaN(d.getTime())) return timeStr; // 防止解析失败
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours().toString().padStart(2, '0')}时${d.getMinutes().toString().padStart(2, '0')}分${d.getSeconds().toString().padStart(2, '0')}秒`;
}

// 🌟 核心提取 1：从登录缓存中拿到角色 (login.vue 里你存了 sessionStorage.setItem("role", data.role))
const userRole = ref(sessionStorage.getItem('role') || 'user')
const token = sessionStorage.getItem("token")

const historyType = ref('temp') // 默认选中温度
const historyData = ref([])     // 存放长长的历史数组

const thresholdTemp = ref(80)
const thresholdDiff = ref(15)
const aiStrategy = ref(true)
const activeMenu = ref('battery1')
const currentDeviceName = ref('1号电池组')

let chartVolListInstance = null;
let chartTempDiffInstance = null;
let chartMainInstance = null;

// ==============================================================================
// 🌟 核心提取 2：究极数据字典扩充！所有硬件团队提到的字段，必须在这里占位！绝不硬编码！
// ==============================================================================
const kpi = ref({
  soc: 0, soh: 0, remain_time: '0h 0m',
  total_capacity: 1000, used_capacity: 0, // 容量类

  current_temp: 0, highest_temp: 0, lowest_temp: 0, temp_diff: 0, // 温度类
  env_temp: 25.0, inlet_temp: '--', outlet_temp: '--', // 环境与风口 (占位)

  total_voltage: 0, total_current: 0, power: 0, power_direction: '静置',
  volt_diff: 0, balance_status: '未开启', // 电压与均衡

  sys_status: '正常', temp_mode: '自然散热', fault_code: '无报警',
  fan_speed: 0, pump_speed: 0, insulation_res: '>500', // 外设与安全

  cell_voltages: [], cell_temps: []
})

const alarm_list = ref([])
const if_stop = ref("no")

let charts = [null, null, null, null, null];
let timer = null;

const deviceMap = {
  'battery1': '1号电池组',
  'battery2': '2号电池组',
  'battery3': '3号电池组',
  'history_battery1': '1号电池组 (历史台账)',
  'history_battery2': '2号电池组 (历史台账)',
  'history_battery3': '3号电池组 (历史台账)'
}


const handleMenuSelect = (index) => {
  activeMenu.value = index;
  if (deviceMap[index]) {
    currentDeviceName.value = deviceMap[index];
    ElMessage.success(`已切换数据源: ${deviceMap[index]}`);

    load_data();
  }
}

const checkToken = () => { if(!token) window.location.href = "/" }

// Echarts 的 options 配置，为了本回合不出错，先保留
const setGlobalOptions = (chart, title, color) => {
  chart.setOption({
    title: { text: title, textStyle: { color: '#94a3b8', fontSize: 13 }, left: 'center', top: '10' },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(30, 41, 59, 0.8)', borderColor: '#1e293b', textStyle: { color: '#f1f5f9' } },
    grid: { left: '12%', right: '5%', bottom: '15%', top: '25%' },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#334155' } } },
    yAxis: { type: 'value', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } } },
    series: [{ data: [], type: 'line', smooth: true, color: color }]
  });
}


const load_data = async () => {
  if(!token) return;
  try {
    const targetDevice = activeMenu.value.replace('history_', '');
    const response = await fetch(`${API_BASE}/data?device=${targetDevice}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    if(data.message == "无权限访问") { window.location.href = "/"; return; }

    const real_data = data.real_data
    const predicts = data.predict_temp

    if(!real_data || real_data.length === 0) return;
    historyData.value = [...real_data].reverse();
    // 取出最新一帧的数据
    const latest = real_data[real_data.length-1];

    // ====================================================================
    // 🔋 1. 给顶部卡片“喂”数据 (全量补齐)
    // ====================================================================
    kpi.value.soc = latest.soc || 0;
    kpi.value.soh = latest.soh || 0;
    kpi.value.used_capacity = kpi.value.total_capacity * (1 - kpi.value.soc / 100);

    if(latest.total_current > 0) {
      const hours = (latest.soc / 100 * kpi.value.total_capacity) / latest.total_current;
      kpi.value.remain_time = `${Math.floor(hours)}h ${Math.floor((hours % 1) * 60)}m`;
    } else {
      kpi.value.remain_time = '静态/充电';
    }

    kpi.value.current_temp = latest.pack_temp || 0;
    kpi.value.highest_temp = latest.highest_temp || 0;
    kpi.value.lowest_temp = latest.lowest_temp || 0;
    kpi.value.temp_diff = kpi.value.highest_temp - kpi.value.lowest_temp; // 🌟 新增：最大温差

    // 硬件还没发这些字段，先接住模拟器发来的，或者用占位符
    kpi.value.env_temp = latest.env_temp ? latest.env_temp.toFixed(1) : 25.0;
    kpi.value.inlet_temp = latest.inlet_temp || '--';
    kpi.value.outlet_temp = latest.outlet_temp || '--';

    kpi.value.fan_speed = latest.fan_speed || 0;
    kpi.value.pump_speed = latest.pump_speed || 0;
    kpi.value.balance_status = latest.balance_status || '关闭';
    kpi.value.insulation_res = latest.insulation_res || '>500';

    kpi.value.total_voltage = latest.total_voltage || 0;
    kpi.value.total_current = latest.total_current || 0;
    kpi.value.power = ((latest.total_voltage * latest.total_current) / 1000).toFixed(2);
    kpi.value.power_direction = latest.total_current > 0 ? '⚡ 放电' : (latest.total_current < 0 ? '🔋 充电' : '静置');

    try {
      kpi.value.cell_voltages = typeof latest.cell_voltages_str === 'string' ? JSON.parse(latest.cell_voltages_str) : (latest.cell_voltages || []);
      // 🌟 新增：计算单体最大压差
      if(kpi.value.cell_voltages.length > 0) {
        kpi.value.volt_diff = Math.max(...kpi.value.cell_voltages) - Math.min(...kpi.value.cell_voltages);
      }
    } catch(e) { kpi.value.cell_voltages = []; kpi.value.volt_diff = 0; }

    if (if_stop.value === 'no' || kpi.value.cell_temps.length === 0) {
      kpi.value.cell_temps = latest.cell_temps || Array.from({length: 12}, () => (latest.lowest_temp + Math.random() * kpi.value.temp_diff).toFixed(1));
    }

    // ====================================================================
    // 🚨 2. 多维状态判定引擎 (全面涵盖温度、电压、电流)
    // ====================================================================
    let current_faults = [];

    // 🌡️ 温度诊断
    if (latest.highest_temp >= thresholdTemp.value) { current_faults.push('热失控'); kpi.value.temp_mode = '满载散热'; }
    else if (latest.highest_temp >= 55) { current_faults.push('高温预警'); kpi.value.temp_mode = '制冷'; }
    else if (latest.lowest_temp <= 10) { current_faults.push('低温限制'); kpi.value.temp_mode = '加热保温'; }
    else { kpi.value.temp_mode = '自然散热'; }

    // ⚡ 电压诊断 (假设额定 410V，上限 430，下限 350)
    if (latest.total_voltage > 430) current_faults.push('总压过高');
    if (latest.total_voltage < 350) current_faults.push('总压欠压');
    if (kpi.value.volt_diff > 0.5) current_faults.push('单体压差过大'); // 压差 > 0.5V 极其危险

    // 🌊 电流诊断 (假设持续最大放电 150A)
    if (Math.abs(latest.total_current) > 150) current_faults.push('短路/严重过流');
    else if (Math.abs(latest.total_current) > 100) current_faults.push('过流预警');

    if (current_faults.length > 0) {
      // 只要触发了严重故障(如热失控、过压)，系统状态就变红
      kpi.value.sys_status = (latest.highest_temp >= thresholdTemp.value || latest.total_voltage > 430 || Math.abs(latest.total_current) > 150) ? '一级故障' : '异常预警';
      kpi.value.fault_code = current_faults.join(' | ');
    } else {
      kpi.value.sys_status = '正常';
      kpi.value.fault_code = '无报警';
    }

    if (latest.highest_temp >= thresholdTemp.value) {
      triggerAlarm(`【紧急】核心温度突破 ${latest.highest_temp}℃，触发熔断停机！`);

      if (if_stop.value === 'no') {
        // 这里的提示保留
        ElMessage.error("🔥 检测到热失控，系统正在强行接管拉闸...");

        // 🌟 核心修复 2：传入 'auto' 暗号，代表这是系统自动触发的！
        if_stop_battery('auto');
      }
    }
    // ====================================================================
    // 📊 3. 运维端图表专属渲染 (权限隔离！只在 Admin 时才消耗浏览器性能画图)
    // ====================================================================
    if (userRole.value === 'admin') {
      const time = real_data.map(item => item.time.substring(11, 19));
      const highest_temps = real_data.map(item => item.highest_temp);
      const currents = real_data.map(item => item.total_current);
      const voltages = real_data.map(item => item.total_voltage);
      const cell_labels = ['芯1','芯2','芯3','芯4','芯5','芯6','芯7','芯8','芯9','芯10','芯11','芯12'];

      if(charts[0]) charts[0].setOption({
        xAxis: { data: [...time, "推-1", "推-2", "推-3", "推-4", "推-5"] },
        series: [
          { name: "单体最高温度", data: highest_temps, color: '#10b981', symbolSize: 8, areaStyle: { opacity: 0.1 } },
          { name: "LSTM多维预测<div class=\"center-panel chart-box main-chart-box\">预测", data: [...Array(highest_temps.length-1).fill(null), highest_temps[highest_temps.length-1], ...predicts], type: 'line', smooth: true, color: '#ef4444', lineStyle: { type: 'dashed', width: 2 } }
        ]
      });

      // 左翼图 1：单体温度列表 (硬件团队要求的 Bar 图)
      if(charts[1]) charts[1].setOption({
        xAxis: { data: cell_labels },
        series: [{ type: 'bar', data: kpi.value.cell_temps, itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] } }]
      });

      // 左翼图 2：充放电电流历史曲线 (硬件团队要求)
      if(charts[2]) charts[2].setOption({ xAxis: { data: time }, series: [{ data: currents, color: '#06b6d4', areaStyle: { opacity: 0.1 } }] });

      // 右翼图 1：单体电压列表 (硬件团队要求的 Bar 图)
      if(charts[3]) charts[3].setOption({
        xAxis: { data: cell_labels },
        yAxis: { min: 2.5 }, // 电压不能从 0 开始看，落差不明显
        series: [{ type: 'bar', data: kpi.value.cell_voltages, itemStyle: { color: '#f97316', borderRadius: [4, 4, 0, 0] } }]
      });

      // 右翼图 2：历史总电压趋势 (硬件团队要求)
      if(charts[4]) charts[4].setOption({ xAxis: { data: time }, series: [{ data: voltages, color: '#10b981', areaStyle: { opacity: 0.1 } }] });
    }

  } catch (error) {
    console.error("加载数据报错啦:", error);
  }
}

const triggerAlarm = (msg) => {
  const timeStr = new Date().toTimeString().split(' ')[0];
  if(alarm_list.value.length === 0 || alarm_list.value[alarm_list.value.length-1].msg !== msg) {
    alarm_list.value.push({ time: timeStr, msg: msg });
  }
}

const if_start_battery = async () => {
  try {
    const response = await fetch(`${API_BASE}/start`, { method: "POST" });
    if (response.ok) {
      if_stop.value = "no";
      ElMessage.success("指令下发成功，设备已开启");
    }
  } catch (error) {
    ElMessage.error("与后端断开连接！");
  }
}

// 🌟 核心修复 1：给函数增加一个 source（来源）参数，默认值是 'manual'（人工）
const if_stop_battery = async (source = 'manual') => {
  try {
    const response = await fetch(`${API_BASE}/stop`, { method: "POST" });
    if (response.ok) {
      if_stop.value = "yes";

      // 🌟 根据触发来源，弹出不同的专业提示！
      if (source === 'auto') {
        ElMessage.error("🚨 熔断机制生效，AI 已自动切断设备电源！");
      } else {
        ElMessage.warning("🛑 已人工介入，设备已强行关停");
      }
    }
  } catch (error) {
    ElMessage.error("与后端断开连接！");
  }
}

// 🌟 新增：专门处理手机屏幕旋转、缩放时的图表重绘引擎
const handleResize = () => {
  charts.forEach(chart => {
    if (chart) {
      chart.resize(); // 强迫图表重新适应手机屏幕大小
    }
  });
};

onMounted(() => {
  checkToken()

  if(userRole.value === 'admin') {
    setTimeout(() => {
      charts[0] = echarts.init(document.getElementById('mainChart'))
      setGlobalOptions(charts[0], '实时温度与 LSTM 多维预判分析', '#10b981')

      charts[1] = echarts.init(document.getElementById('chartLeft1'))
      setGlobalOptions(charts[1], '实时单体温度监控分布 (℃)', '#3b82f6')

      charts[2] = echarts.init(document.getElementById('chartLeft2'))
      setGlobalOptions(charts[2], '系统充放电电流走势 (A)', '#06b6d4')

      charts[3] = echarts.init(document.getElementById('chartRight1'))
      setGlobalOptions(charts[3], '实时单体电压监控分布 (V)', '#f97316')

      charts[4] = echarts.init(document.getElementById('chartRight2'))
      setGlobalOptions(charts[4], '系统总压浮动趋势 (V)', '#10b981')
    }, 100);
  }

  load_data()
  timer = setInterval(load_data, 2000)

  // 监听浏览器窗口大小变化
  window.addEventListener('resize', handleResize);
})

// 🌟 清理工作：离开页面时销毁监听器
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (timer) clearInterval(timer);
})
</script>

<style scoped>
/* ==============================================================
   🎨 全局基础样式与毛玻璃面板
   ============================================================== */
:deep(.el-container) { background-color: transparent !important; }

.layout-container {
  height: 100vh;
  background-color: #020617;
  background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 25px 25px;
  color: #f1f5f9;
}

.glass-panel {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -4px rgba(0, 0, 0, 0.2);
}

/* ==============================================================
   🎨 左侧侧边栏与顶部 Header
   ============================================================== */
.aside-menu {
  background: rgba(15, 23, 42, 0.8) !important;
  border-right: 1px solid rgba(16, 185, 129, 0.2) !important;
}
.system-title {
  height: 60px; display: flex; align-items: center; justify-content: center;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.05); margin-bottom: 10px;
}
.system-title .logo { font-size: 28px; }
.system-title .text {
  font-size: 20px; font-weight: 800; background: linear-gradient(120deg, #10b981, #3b82f6);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-left: 8px;
}
:deep(.el-menu) { border-right: none !important; }
:deep(.el-sub-menu__title:hover), :deep(.el-menu-item:hover) { background-color: rgba(16, 185, 129, 0.1) !important; color: #f1f5f9 !important; }
:deep(.el-menu-item) { height: 50px; background-color: transparent !important; }
:deep(.el-menu-item.is-active) { border-left: 3px solid #10b981; }

.main-header {
  background: rgba(15, 23, 42, 0.8) !important;
  border-bottom: 1px solid rgba(16, 185, 129, 0.2) !important;
  display: flex; align-items: center; justify-content: space-between;
}
.page-title { margin: 0; color: #e2e8f0; letter-spacing: 1px; }

/* ==============================================================
   🎨 模块 1：顶部高密度 KPI 卡片组
   ============================================================== */
.flex-around { display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px; }
.kpi-container { margin-bottom: 20px; }
.kpi-card { width: calc(20% - 12px); padding: 15px; position: relative; }

.tech-corner::before, .tech-corner::after { content: ''; position: absolute; width: 10px; height: 10px; border: 2px solid transparent; }
.tech-corner::before { top: 0; left: 0; border-top-color: #10b981; border-left-color: #10b981; }
.tech-corner::after { bottom: 0; right: 0; border-bottom-color: #3b82f6; border-right-color: #3b82f6; }

.kpi-header { font-size: 12px; color: #94a3b8; display: flex; align-items: center; margin-bottom: 8px; font-weight: bold; }
.blink-dot { width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; animation: breath 2s infinite ease-in-out; box-shadow: 0 0 8px currentColor; }
.dot-green { background-color: #10b981; color: #10b981; }
.dot-blue { background-color: #3b82f6; color: #3b82f6; }
.dot-orange { background-color: #f97316; color: #f97316; }
.dot-cyan { background-color: #06b6d4; color: #06b6d4; }
.dot-red { background-color: #ef4444; color: #ef4444; }
@keyframes breath { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.kpi-main { border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 8px; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 800; }
.kpi-unit { font-size: 12px; color: #64748b; margin-left: 5px; }

.kpi-sub-list { display: flex; flex-direction: column; gap: 5px; }
.sub-item { display: flex; justify-content: space-between; font-size: 11px; color: #64748b; background: rgba(0, 0, 0, 0.2); padding: 4px 6px; border-radius: 4px; }
.sub-item span:last-child { color: #cbd5e1; font-weight: bold; font-family: monospace; }

.text-green { color: #10b981 !important; text-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }
.text-blue { color: #3b82f6 !important; text-shadow: 0 0 10px rgba(59, 130, 246, 0.4); }
.text-orange { color: #f97316 !important; text-shadow: 0 0 10px rgba(249, 115, 22, 0.4); }
.text-cyan { color: #06b6d4 !important; text-shadow: 0 0 10px rgba(6, 182, 212, 0.4); }
.text-safe { color: #10b981 !important; }
.text-danger { color: #ef4444 !important; text-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }
.text-light { color: #f8fafc !important; }
.safe-border { border-top: 2px solid #10b981 !important; }
.danger-border { border-top: 2px solid #ef4444 !important; box-shadow: inset 0 0 15px rgba(239,68,68,0.2) !important; }

/* ==============================================================
   🎨 模块 2：中央 3 栏图表矩阵
   ============================================================== */
.middle-matrix { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 20px; height: 420px; }
.wing-panel { width: 25%; display: flex; flex-direction: column; gap: 15px; }
.center-panel { width: 50%; }
.chart-box { flex: 1; width: 100%; padding: 10px; box-sizing: border-box; }
.main-chart-box { height: 100%; width: 100%; padding: 15px; box-sizing: border-box; box-shadow: inset 0 0 20px rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); }

/* ==============================================================
   🎨 模块 3：底部日志与控制区
   ============================================================== */
.flex-between { display: flex; justify-content: space-between; gap: 15px; }
.alarm-box { width: 75%; height: 180px; padding: 15px; box-sizing: border-box; }
.alarm-box h3 { margin: 0 0 10px 0; color: #f8fafc; font-size: 16px; border-left: 3px solid #ef4444; padding-left: 8px; }
.alarm-list { height: 120px; overflow-y: auto; }
.y_alarm { display: flex; gap: 15px; padding: 6px 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.05); }
.alarm_time { color: #64748b; font-size: 12px; font-family: monospace; }
.alarm_msg { font-size: 13px; font-weight: bold; color: #cbd5e1; }

.control-box { width: 25%; height: 180px; display: flex; align-items: center; justify-content: center; }
.control-btn { width: 180px; height: 50px; font-size: 16px; font-weight: bold; border-radius: 8px; box-shadow: 0 8px 15px rgba(0,0,0,0.4); }
.shake-btn:hover { animation: mini-shake 0.3s infinite; }
@keyframes mini-shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(1px); } 75% { transform: translateX(-1px); } }

:deep(.el-tag--dark.el-tag--success) { background-color: #064e3b; border-color: #065f46; color: #10b981; }
:deep(.el-button--danger) { background: linear-gradient(135deg, #ef4444, #dc2626) !important; border: none !important; }
:deep(.el-button--success) { background: linear-gradient(135deg, #10b981, #059669) !important; border: none !important; }
.alarm-list::-webkit-scrollbar { width: 4px; }
.alarm-list::-webkit-scrollbar-thumb { background-color: #334155; border-radius: 2px; }




:deep(.dark-table) { background-color: transparent !important; --el-table-border-color: rgba(255, 255, 255, 0.05); --el-table-header-bg-color: rgba(15, 23, 42, 0.9); --el-table-row-hover-bg-color: rgba(16, 185, 129, 0.1); }
:deep(.dark-table th.el-table__cell) { background-color: rgba(0, 0, 0, 0.4) !important; color: #10b981; border-bottom: 1px solid rgba(16, 185, 129, 0.3); }
:deep(.dark-table tr) { background-color: transparent !important; color: #cbd5e1; }
:deep(.dark-table td.el-table__cell) { border-bottom: 1px dashed rgba(255, 255, 255, 0.05); }
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) { background: rgba(255, 255, 255, 0.02) !important; }
/* 隐藏表格底部的白边 */
:deep(.el-table__inner-wrapper::before) { display: none; }

@media screen and (max-width: 768px) {
  /* 1. 整体变成上下滚动 */
  .layout-container { flex-direction: column; height: auto; min-height: 100vh; overflow-y: auto; }

  /* 2. 菜单变成顶部导航 */
  .aside-menu { width: 100% !important; height: auto; z-index: 10; border-bottom: 1px solid rgba(16, 185, 129, 0.2); }
  :deep(.el-menu) { display: flex; flex-wrap: wrap; justify-content: center; }
  :deep(.el-menu-item) { padding: 0 10px !important; }

  /* 3. 顶部数据卡片占满全宽 */
  .kpi-card { width: 100% !important; margin-bottom: 15px; }

  /* 4. 🌟 核心修复：把 3 列图表解绑成上下堆叠，必须强制给高度！ */
  .middle-matrix { flex-direction: column !important; height: auto !important; margin-bottom: 20px; }
  .wing-panel, .center-panel { width: 100% !important; height: auto !important; }

  /* 🌟 致命错误解决：给每个图表容器写死高度，否则高度为 0 就画不出图 */
  .chart-box { height: 300px !important; width: 100% !important; margin-bottom: 15px; }
  .main-chart-box { height: 350px !important; width: 100% !important; margin-bottom: 15px; }

  /* 5. 底部报警区 */
  .flex-between { flex-direction: column; }
  .alarm-box, .control-box { width: 100% !important; height: auto !important; }
  .control-box { padding-top: 15px; margin-bottom: 30px; }
  .control-btn { width: 100% !important; margin-left: 0 !important; }
}
</style>
