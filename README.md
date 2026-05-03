# 项目代码阅读说明

## 1. 项目整体结构

本项目是一个“前后端分离 + MQTT 实时数据接入 + InfluxDB 时序存储 + MySQL 登录鉴权 + LSTM 温度预测”的电池热管理监控系统。

目录结构如下：

```text
竞赛前后端开发/
├─ backend/
│  ├─ server.py                 # FastAPI 后端主程序
│  └─ requirements.txt          # Python 依赖清单
├─ device/
│  └─ simulator.py              # 模拟设备数据上报脚本
├─ LSTM模型/
│  ├─ best_battery_lstm.pth     # 训练好的 LSTM 权重
│  ├─ scaler_X.pkl              # 输入特征归一化器
│  └─ scaler_Y.pkl              # 输出温度反归一化器
├─ web/
│  ├─ package.json              # 前端依赖与脚本
│  ├─ vite.config.js            # Vite 构建配置
│  └─ src/
│     ├─ main.js                # Vue 入口
│     ├─ App.vue                # 根组件
│     ├─ router/index.ts        # 路由与前端登录拦截
│     └─ components/
│        ├─ login.vue           # 登录页
│        └─ dashboard.vue       # 监控大屏
└─ docker-compose.yml           # MySQL / InfluxDB / MQTT 基础服务编排
```

---

## 2. 系统角色分工

### 前端 `web`

前端使用 Vue 3 + Vite + Element Plus + ECharts。

职责：

- 提供登录页和监控大屏。
- 调用后端 `/login`、`/data`、`/start`、`/stop` API。
- 将后端返回的实时数据和预测结果渲染成 KPI 卡片、告警信息和图表。

### 后端 `backend/server.py`

后端使用 FastAPI，但它不仅仅是一个 HTTP API 服务，还承担了多个角色：

- 启动时加载 LSTM 模型和归一化器。
- 建立 MQTT 连接，订阅设备数据主题。
- 将接收到的实时数据写入 InfluxDB。
- 提供登录接口，访问 MySQL 用户表。
- 提供实时数据接口，查询 InfluxDB 并调用 LSTM 做温度预测。
- 提供设备启停控制接口，通过 MQTT 发布控制消息。
- 在高温达到阈值时触发钉钉告警，并自动下发停机指令。

### 设备模拟器 `device/simulator.py`

模拟器持续生成 3 组电池数据并发布到 MQTT，用来驱动整套演示链路。

职责：

- 按时间阶段构造正常、预警、热失控三种状态数据。
- 生成 `battery1`、`battery2`、`battery3` 三个设备的数据。
- 订阅 `start/stop` 控制主题，根据控制消息暂停或恢复上报。

### 模型目录 `LSTM模型`

这里不是服务，而是后端启动时会直接读取的推理资源：

- `best_battery_lstm.pth`：LSTM 网络权重。
- `scaler_X.pkl`：输入特征标准化器。
- `scaler_Y.pkl`：预测结果反标准化器。

---

## 3. 一条完整的数据链路

这个项目最关键的是读懂“数据怎么流动”。

### 链路 1：实时采集与展示

```text
device/simulator.py
  -> MQTT 主题 battery/data
  -> backend/server.py 的 on_message()
  -> 写入 InfluxDB measurement=battery
  -> 前端 dashboard.vue 轮询 GET /data
  -> FastAPI 查询 InfluxDB 最近 15 条数据
  -> 返回给前端
  -> ECharts/KPI 页面展示
```

### 链路 2：温度预测

```text
前端请求 GET /data?device=battery1
  -> 后端查询该 device 最近 15 条记录
  -> 取最近 10 条作为 LSTM 输入窗口
  -> 提取 6 个特征
     total_voltage
     total_current
     highest_temp
     lowest_temp
     fan_speed
     pump_speed
  -> scaler_X 标准化
  -> LSTM 推理
  -> scaler_Y 反标准化
  -> 返回 3 步预测温度 predict_temp
  -> 前端主图叠加预测曲线
```

### 链路 3：异常告警与停机

```text
模拟器/真实设备上报数据
  -> 后端 MQTT 回调 on_message()
  -> 如果 highest_temp >= 80
     -> send_dingtalk_alarm()
     -> MQTT publish "start/stop" = "stop"
  -> 模拟器收到 stop 后暂停上报
```

### 链路 4：登录鉴权

```text
login.vue 提交用户名密码
  -> POST /login
  -> backend 查询 MySQL user 表
  -> 返回 token + role
  -> 前端 sessionStorage 保存 token / role
  -> dashboard.vue 调 GET /data 时带 Authorization: Bearer <token>
  -> FastAPI 从 OAuth2PasswordBearer 取出 token
  -> token 正确才返回数据
```

---

## 4. 后端代码架构说明

后端只有一个主文件 `backend/server.py`，但逻辑上可以拆成 6 个模块来理解。

### 4.1 模型加载模块

对应代码：

- `BatteryTempPredictor`
- `model.load_state_dict(...)`
- `scaler_X = joblib.load(...)`
- `scaler_Y = joblib.load(...)`

作用：

- 定义 LSTM 网络结构。
- 在服务启动时把模型和归一化器一次性加载进内存。
- 后续 `/data` 接口直接拿来推理，不重复加载。

### 4.2 基础连接初始化模块

对应代码：

- `app = FastAPI()`
- `db = InfluxDBClient(...)`
- `db.switch_database('iot')`
- `client = mqtt.Client()`
- `client.connect(...)`

作用：

- 初始化 HTTP 服务。
- 初始化 InfluxDB 客户端。
- 初始化 MQTT 客户端。

这意味着 `server.py` 启动时，不只是开一个 Web 服务，它还顺带建立了数据库连接和消息总线连接。

### 4.3 MQTT 消费与落库模块

核心函数：

- `on_message(client, userdata, message)`
- `start_mqtt()`

工作流程：

1. 订阅主题 `battery/data`。
2. 收到消息后把 JSON 反序列化成 Python dict。
3. 提取 `device_id`。
4. 如果温度过高，触发告警和停机。
5. 将数据写入 InfluxDB：
   - measurement：`battery`
   - tags：`device_id`
   - fields：除 `device_id` 之外的全部字段

这里的设计要点：

- `device_id` 放在 tag 中，便于按设备查询。
- 其余数值都作为时序字段写入 InfluxDB。
- 后端既是 MQTT 消费者，也是 HTTP API 提供者。

### 4.4 实时数据查询与预测模块

核心接口：

- `@app.get('/data')`

处理流程：

1. 通过 `OAuth2PasswordBearer` 从请求头解析 Bearer Token。
2. token 不等于固定值 `this_is_a_token` 时直接拒绝。
3. 查询 InfluxDB 最近 15 条指定设备的数据。
4. 将查询结果从倒序改回正序。
5. 如果数据条数不少于 10，则执行 LSTM 预测。
6. 返回：

```json
{
  "real_data": [...],
  "predict_temp": [x1, x2, x3]
}
```

这里有一个轻量缓存机制：

- `LAST_DATA_TIME`
- `CACHED_PREDICT`

作用：

- 如果当前请求看到的最新数据时间戳没变，就直接复用上一轮预测结果，避免重复推理。

### 4.5 MySQL 登录模块

核心函数：

- `get_mysql_conn()`
- `@app.post('/login')`

处理流程：

1. 前端以表单方式提交 `username`、`password`。
2. 后端连接 MySQL。
3. 执行 SQL：

```sql
SELECT role FROM user WHERE username=%s AND password=%s
```

4. 查询成功则返回：

```json
{
  "message": "登录成功",
  "token": "this_is_a_token",
  "role": "..."
}
```

这里的鉴权方式非常简单，本质上不是 JWT，也不是数据库会话，而是：

- 登录成功后统一发一个固定 token。
- 后续接口只检查这个固定 token 是否相等。

所以它更接近“演示版令牌认证”。

### 4.6 控制与告警模块

核心内容：

- `send_dingtalk_alarm(...)`
- `@app.post('/stop')`
- `@app.post('/start')`

行为说明：

- `/stop`：向 MQTT 主题 `start/stop` 发布 `stop`
- `/start`：向 MQTT 主题 `start/stop` 发布 `start`
- 高温超过 80 时，也会自动发布 `stop`
- 钉钉告警做了 60 秒内同设备限流，避免刷屏

所以后端同时也是一个“控制指令转发器”。

---

## 5. API 连接方式说明

### 5.1 登录接口

**接口**

```http
POST /login
Content-Type: multipart/form-data
```

**参数**

- `username`
- `password`

**返回**

```json
{
  "message": "登录成功",
  "token": "this_is_a_token",
  "role": "admin"
}
```

### 5.2 实时数据接口

**接口**

```http
GET /data?device=battery1
Authorization: Bearer this_is_a_token
```

**参数**

- `device`：`battery1` / `battery2` / `battery3`

**返回**

- `real_data`：最近 15 条历史数据
- `predict_temp`：预测的未来 3 步温度

### 5.3 启动设备

**接口**

```http
POST /start
```

**作用**

- 向 MQTT 发布 `start`

### 5.4 停止设备

**接口**

```http
POST /stop
```

**作用**

- 向 MQTT 发布 `stop`

---

## 6. 前端怎么接后端

### `login.vue`

登录页做的事情很直接：

1. 用户输入用户名密码。
2. 通过 `fetch(.../login)` 提交表单。
3. 如果成功：
   - `sessionStorage.setItem("token", data.token)`
   - `sessionStorage.setItem("role", data.role)`
4. 跳转到 `/dashboard`

### `router/index.ts`

前端路由只有两个页面：

- `/login`
- `/dashboard`

并且做了一个简单前置守卫：

- 如果访问 `/dashboard` 时本地没有 `token`
- 就强制跳回 `/login`

所以前端的“登录态”完全保存在浏览器 `sessionStorage` 中。

### `dashboard.vue`

这是整个前端最核心的页面。

它主要做 5 件事：

1. 每 2 秒调用一次 `/data`
2. 用返回的 `real_data` 更新顶部 KPI
3. 用 `predict_temp` 更新主图预测曲线
4. 根据温度、电压、电流做前端二次故障判定
5. 调用 `/start`、`/stop` 控制设备

也就是说，后端负责“原始数据接入 + 存储 + 预测”，前端负责“展示 + 二次状态解释 + 图表编排”。

---

## 7. InfluxDB 数据模型

后端写入 InfluxDB 时，measurement 固定为：

```text
battery
```

tag：

- `device_id`

field 示例：

- `soc`
- `soh`
- `env_temp`
- `highest_temp`
- `lowest_temp`
- `pack_temp`
- `total_voltage`
- `total_current`
- `fan_speed`
- `pump_speed`
- `inlet_temp`
- `outlet_temp`
- `insulation_res`
- `balance_status`
- `cell_temps_str`
- `cell_voltages_str`

查询逻辑是：

```sql
select * from battery
where "device_id" = 'battery1'
order by time desc
limit 15
```

这个设计说明：

- InfluxDB 是整个系统的“实时历史库”。
- 前端看到的所有图表基础数据，都是从 InfluxDB 读出来的，而不是直接从 MQTT 实时推送到浏览器。

---

## 8. MQTT 主题设计

当前代码里可以看见两个主题：

### 上行数据主题

```text
battery/data
```

用途：

- 设备或模拟器发布遥测数据
- 后端订阅并处理

### 下行控制主题

```text
start/stop
```

用途：

- 后端发布控制命令
- 模拟器订阅命令并执行暂停/恢复

所以项目里的 MQTT 是双向的：

- `device -> backend`：上报数据
- `backend -> device`：控制启停

---

## 9. 模拟器数据是怎么构造的

`device/simulator.py` 不是简单随机数，而是按阶段构造了一个“有剧情”的数据流。

### 阶段 1：正常运行

- 温度缓慢上升
- 电流较小
- 风扇和水泵低速
- 单体电压波动较小

### 阶段 2：二级预警

- 温度明显抬升
- 电流增大
- 风扇和水泵转速提升
- 某单体电压开始异常

### 阶段 3：热失控触发期

- 最高温快速飙升
- 电流进一步增大
- 电压下降
- 某单体电压显著异常
- 绝缘电阻恶化

随后每秒发布 3 份数据：

- `battery1`：基准设备
- `battery2`：温度略低
- `battery3`：电流为负，模拟充电状态

这套设计是为了让前端大屏能明显展示“正常 -> 预警 -> 故障”的演化过程。

---

## 10. 代码中的几个关键设计点

### 10.1 为什么后端既有 MQTT 又有 HTTP

因为这个系统本质上分两类通信：

- 设备侧适合用 MQTT 做持续上报和控制
- 浏览器侧适合用 HTTP API 做轮询访问

所以后端其实扮演了“协议转换中枢”的角色：

```text
MQTT 世界 <-> FastAPI 后端 <-> HTTP 世界
```

### 10.2 为什么先写 InfluxDB 再给前端查

因为这样可以同时满足：

- 实时展示
- 历史回放
- 模型预测的时间窗口输入

如果直接 MQTT 推给前端，后端就不容易统一做：

- 历史查询
- 设备切换
- 模型输入窗口管理

### 10.3 为什么预测逻辑放在 `/data` 里

这是一个“边查询边推理”的设计：

- 前端请求一次数据
- 后端顺便把预测也做掉
- 前端无需再单独请求一个 `/predict`

好处是调用简单。
代价是 `/data` 的职责变得较重。

---

## 11. 当前后端架构的优点与局限

### 优点

- 代码集中，演示项目容易跑通。
- 设备数据接入、落库、预测、告警、API 输出串得很顺。
- 数据链路清晰，便于比赛展示。
- 前端页面效果集中，适合大屏演示。

### 局限

- 后端所有逻辑都堆在 `server.py` 中，耦合较高。
- 登录认证是固定 token，不适合正式生产。
- 预测逻辑、MQTT 消费、数据库访问、告警逻辑没有分层。
- 缺少独立的 service / repository / model / router 模块划分。
- 当前异常处理比较粗，很多地方更偏演示逻辑。

---

## 12. 如果把后端按“架构视角”重命名，可以理解成这样

虽然代码只有一个文件，但逻辑上已经具备这些层次：

### 接入层

- FastAPI 路由
- MQTT 消费回调

### 数据层

- InfluxDB 时序读写
- MySQL 用户查询

### 业务层

- 温度阈值判断
- 启停逻辑
- 告警逻辑
- 预测逻辑

### 算法层

- LSTM 模型推理
- scaler 标准化 / 反标准化

### 表现层

- Vue 仪表盘
- ECharts 图表
- KPI 与告警展示

---

## 13. 一句话总结这套系统

这套代码的核心不是“单纯的前后端项目”，而是一套围绕电池状态监控构建的“数据采集 -> 落库 -> 预测 -> 告警 -> 控制 -> 可视化展示”的闭环演示系统。

后端的本质作用，是把：

- 设备世界的 MQTT 数据
- 时序库里的历史记录
- AI 模型的预测能力
- 浏览器页面的展示需求

统一串成一条完整的数据链路。

