import influxdb
import pymysql
from fastapi import FastAPI, Form, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from influxdb import InfluxDBClient
import paho.mqtt.client as mqtt
import json
import torch
import torch.nn as nn
import numpy as np
import joblib
import pandas as pd
import requests
import time
from datetime import datetime

# =========================================================
# 🌟 1. 定义 LSTM 模型结构 (必须跟训练时完全一致)
# =========================================================
class BatteryTempPredictor(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=64, output_dim=3, num_layers=1):
        super(BatteryTempPredictor, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        predictions = self.fc(out)
        return predictions

# =========================================================
# 🌟 2. 提前加载模型大脑和“两把尺子” (替代原来的 Chronos)
# =========================================================
print("正在加载 AI 预测引擎...")
model = BatteryTempPredictor()
model.load_state_dict(torch.load("../LSTM模型/best_battery_lstm.pth"))
model.eval()  # 设置为推理模式

scaler_X = joblib.load("../LSTM模型/scaler_X.pkl")
scaler_Y = joblib.load("../LSTM模型/scaler_Y.pkl")
print("✅ LSTM 模型与归一化工具加载完毕！")

app = FastAPI()
db = InfluxDBClient(host='localhost', port=8086)
db.switch_database('iot')

client = mqtt.Client()
client.connect("localhost", 1884, 60)

dingding = "https://oapi.dingtalk.com/robot/send?access_token=f1d6ffa38b1335c04de55c525f0cb79ced807df74bbeb3243729e72ab5271f0b"

last_alarm_time = {}

def send_dingtalk_alarm(device_id, temp, msg):
    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_time = time.time()

    if device_id in last_alarm_time and current_time - last_alarm_time[device_id] < 60:
        return

    last_alarm_time[device_id] = current_time

    payload = {
        "msgtype": "text",
        "text": {
            "content": (
                f"【温控有锂-紧急报警】\n"
                f"报警时间：{now_time}\n"  
                f"设备ID：{device_id}\n"
                f"当前最高温：{temp}℃\n"
                f"状态：{msg}\n"
            )
        }
    }
    headers = {'Content-Type': 'application/json'}

    try:
        requests.post(dingding, json=payload, headers=headers)
        print(f"钉钉报警已发送！设备：{device_id}，温度：{temp}")
    except Exception as e:
        print(f"钉钉报警发送失败: {e}")


data_buckets = {
    "battery1": [],
    "battery2": [],
    "battery3": []
}

def on_message(client, userdata, message):
    data = json.loads(message.payload.decode())
    device_id = data.get('device_id', 'unknown_device')

    highest_temp = data.get('highest_temp', 0)
    # 如果核心温度突破 80 度
    if highest_temp >= 80.0:
        send_dingtalk_alarm(device_id, highest_temp, "检测到热失控，触发熔断停机！")

        client.publish("start/stop", "stop")

    if device_id in data_buckets:
        data_buckets[device_id].append(data)
        if len(data_buckets[device_id]) > 180:
            data_buckets[device_id].pop(0)

    fields = {k: v for k, v in data.items() if k != 'device_id'}
    body = {
        "measurement": "battery",
        "tags": {"device_id": device_id},
        "fields": fields
    }
    db.write_points([body])

def start_mqtt():
    client.subscribe("battery/data")
    client.on_message = on_message
    client.loop_start()

start_mqtt()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

LAST_DATA_TIME = None
CACHED_PREDICT = []

permission = OAuth2PasswordBearer(tokenUrl="/token")

@app.get('/data')
def index(device: str = 'battery1', token: str = Depends(permission)):
    global LAST_DATA_TIME, CACHED_PREDICT
    if token != "this_is_a_token":
        return {"message": "无权限访问"}

    # 依然查询 15 条，满足前端画图需求
    query_sql = f"select * from battery where \"device_id\" = '{device}' order by time Desc limit 15"
    data = db.query(query_sql)
    real_data = list(data.get_points())
    real_data.reverse()  # 翻转为按时间正序排列

    predicted_temps = []

    try:
        # 我们的 LSTM 模型需要正好 10 条历史数据
        if len(real_data) >= 10:
            latest_time = str(real_data[-1]['time']) + "_" + device

            if latest_time != LAST_DATA_TIME:
                # 🌟 核心手术：提取模型需要的 6 个特征 (一定要按训练时的严格顺序！)
                feature_names = ['total_voltage', 'total_current', 'highest_temp', 'lowest_temp', 'fan_speed', 'pump_speed']

                # 截取最近的 10 条数据
                recent_10_data = real_data[-10:]
                input_data = []

                for item in recent_10_data:
                    row = [
                        item.get('total_voltage', 0),
                        item.get('total_current', 0),
                        item.get('highest_temp', 0),
                        item.get('lowest_temp', 0),
                        item.get('fan_speed', 0),
                        item.get('pump_speed', 0)
                    ]
                    input_data.append(row)

                # 转换为 DataFrame 喂给 scaler_X，防止报特征名缺失的警告
                input_df = pd.DataFrame(input_data, columns=feature_names)
                input_scaled = scaler_X.transform(input_df)

                # 转换为 PyTorch Tensor (形状: 1批次, 10时间步, 6特征)
                input_tensor = torch.tensor([input_scaled], dtype=torch.float32)

                # 🌟 让模型闭卷预测
                with torch.no_grad():
                    pred_scaled = model(input_tensor)

                # 🌟 使用 scaler_Y 将预测出的小数变回真实的摄氏度
                pred_real = scaler_Y.inverse_transform(pred_scaled.numpy())

                # 整理最终的 3 个温度数值并加以安全限制
                predicted_temps = [round(float(val), 1) for val in pred_real[0]]
                predicted_temps = [min(val, 200.0) for val in predicted_temps]

                CACHED_PREDICT = predicted_temps
                LAST_DATA_TIME = latest_time
            else:
                predicted_temps = CACHED_PREDICT
        else:
            # 如果刚开机数据库里数据还不够 10 条，先用最后一条温度凑合一下
            predicted_temps = [real_data[-1].get('highest_temp', 0)] * 3 if real_data else []

    except Exception as e:
        print(f"AI 预测报错啦: {e}")
        predicted_temps = [real_data[-1].get('highest_temp', 0)] * 3 if real_data else []

    return {
        "real_data": real_data,
        "predict_temp": predicted_temps
    }

def get_mysql_conn():
    return pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='root123',
        database='iot_system',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.post('/login')
def login(username: str = Form(...), password: str = Form(...)):
    conn = None
    cursor = None
    try:
        conn = get_mysql_conn()
        cursor = conn.cursor()
        sql = "SELECT role FROM user WHERE username=%s AND password=%s"
        cursor.execute(sql, (username, password))
        user = cursor.fetchone()
        if user:
            return {
                "message": "登录成功",
                "token": "this_is_a_token",
                "role": user["role"]
            }
        else:
            return {"message": "账号或密码错误"}
    except Exception as e:
        return {"message": f"数据库错误: {str(e)}"}
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.post('/stop')
def stop():
    client.publish("start/stop", "stop")
    return {"message": "关闭成功"}

@app.post('/start')
def start():
    client.publish("start/stop", "start")
    return {"message": "开启成功"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)