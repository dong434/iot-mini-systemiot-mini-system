import random
import json
import paho.mqtt.client as mqtt
import time
import math

TOTAL_STEPS = 120

arrays = {
    "soc": [max(85.0 - i * 0.05, 0) for i in range(TOTAL_STEPS)],
    "soh": [98.0 for _ in range(TOTAL_STEPS)],
    "env_temp": [28.0 + random.uniform(-0.5, 0.5) for _ in range(TOTAL_STEPS)],
    "total_voltage": [],
    "total_current": [],
    "highest_temp": [],
    "lowest_temp": [],
    "pack_temp": [],
    "fan_speed": [],
    "pump_speed": [],
    "cell_voltages": []
}

for i in range(TOTAL_STEPS):
    # 【0-60秒】：正常运行期
    if i <= 60:
        base_temp = 35.0 + (i * 0.1)
        arrays["highest_temp"].append(round(base_temp + random.uniform(0, 1), 1))
        arrays["lowest_temp"].append(round(33.0 + (i * 0.05), 1))
        arrays["total_current"].append(round(30.0 + random.uniform(-2, 2), 1))
        arrays["total_voltage"].append(round(410.0 - (i * 0.1), 1))
        arrays["fan_speed"].append(1200 + int(i * 10))
        arrays["pump_speed"].append(15 + i * 0.1)
        arrays["cell_voltages"].append([round(3.4 + random.uniform(-0.05, 0.05), 2) for _ in range(12)])

    # 【60-90秒】：二级预警期
    elif i <= 90:
        base_temp = arrays["highest_temp"][-1] + 0.8
        arrays["highest_temp"].append(round(base_temp + random.uniform(0, 2), 1))
        arrays["lowest_temp"].append(round(arrays["lowest_temp"][-1] + 0.2, 1))
        arrays["total_current"].append(round(45.0 + random.uniform(5, 10), 1))
        arrays["total_voltage"].append(round(arrays["total_voltage"][-1] - 0.5, 1))
        arrays["fan_speed"].append(3500)
        arrays["pump_speed"].append(30.0)
        cells = [round(3.3 + random.uniform(-0.1, 0.1), 2) for _ in range(12)]
        cells[4] = round(3.0 + random.uniform(-0.1, 0.1), 2)
        arrays["cell_voltages"].append(cells)

    # 【90-120秒】：热失控触发期
    else:
        base_temp = arrays["highest_temp"][-1] + 1.5
        arrays["highest_temp"].append(round(base_temp, 1))
        arrays["lowest_temp"].append(round(arrays["lowest_temp"][-1] + 0.5, 1))
        arrays["total_current"].append(round(80.0 + random.uniform(10, 20), 1))
        arrays["total_voltage"].append(round(arrays["total_voltage"][-1] - 2.0, 1))
        arrays["fan_speed"].append(5000)
        arrays["pump_speed"].append(45.0)
        cells = [round(3.2 + random.uniform(-0.2, 0.2), 2) for _ in range(12)]
        cells[4] = round(1.5 + random.uniform(-0.5, 0.5), 2)
        arrays["cell_voltages"].append(cells)

    arrays["pack_temp"].append(round((arrays["highest_temp"][-1] + arrays["lowest_temp"][-1]) / 2, 1))


client = mqtt.Client()
client.connect("127.0.0.1", 1884, 60)

order = "start"
def on_message(client, userdata, message):
    global order
    order = message.payload.decode()

client.subscribe("start/stop")
client.on_message = on_message
client.loop_start()

step_index = 0
while True:
    if order == "stop":
        time.sleep(0.1)
        continue

    if step_index >= TOTAL_STEPS:
        step_index = 0

    # 🌟 提取基础剧本数据
    pack_t = arrays["pack_temp"][step_index]
    volt_list = arrays["cell_voltages"][step_index]

    # 🌟 补全所有缺失的周边维度数据
    base_data = {
        "soc": arrays["soc"][step_index],
        "soh": arrays["soh"][step_index],
        "env_temp": arrays["env_temp"][step_index],
        "highest_temp": arrays["highest_temp"][step_index],
        "lowest_temp": arrays["lowest_temp"][step_index],
        "pack_temp": pack_t,
        "total_voltage": arrays["total_voltage"][step_index],
        "total_current": arrays["total_current"][step_index],
        "fan_speed": arrays["fan_speed"][step_index],
        "pump_speed": arrays["pump_speed"][step_index],

        # 补全：进出风口温度（基于包内均温推算）
        "inlet_temp": round(pack_t - random.uniform(3.0, 5.0), 1),
        "outlet_temp": round(pack_t + random.uniform(2.0, 4.0), 1),

        # 补全：绝缘电阻 (正常>500，热失控时急剧下降)
        "insulation_res": round(random.uniform(600, 800) if step_index < 90 else random.uniform(50, 200), 1),

        # 补全：均衡状态 (压差>0.2V时开启)
        "balance_status": "开启" if max(volt_list) - min(volt_list) > 0.2 else "关闭",

        # 补全：单体温度数组 (12节电芯)
        "cell_temps_str": json.dumps([round(random.uniform(arrays["lowest_temp"][step_index], arrays["highest_temp"][step_index]), 1) for _ in range(12)]),

        "cell_voltages_str": json.dumps(volt_list)
    }

    # 发布数据
    data1 = {**base_data, "device_id": "battery1"}
    data2 = {**base_data, "device_id": "battery2", "highest_temp": round(base_data["highest_temp"] - 5.0, 1)}
    data3 = {**base_data, "device_id": "battery3", "total_current": -25.0}

    client.publish("battery/data", json.dumps(data1))
    client.publish("battery/data", json.dumps(data2))
    client.publish("battery/data", json.dumps(data3))

    print(f"▶️ 第 {step_index} 帧发送完毕 -> [1号状态模拟完全拉满]")

    step_index += 1
    time.sleep(1)

