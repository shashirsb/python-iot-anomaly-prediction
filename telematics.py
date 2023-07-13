import requests
import io
import json
import logging

#from fdk import response

iot_data = "7E0200005600880678855500D300000000000400030130A46D04651F8002860000000022050916314401040000000A03020000E40203202504000000002B040000000030010031010B160400000068170101180401000000140400000002EA030000022F7E"

data = {
"start_marker": iot_data[0:2],
"message_id": iot_data[2:6],
"message_atr": iot_data[6:10],
"device_phone_no": iot_data[10:22],
"message_sr_no": iot_data[22:26],
"alarm_sign": iot_data[26:34],
"status": iot_data[34:42],
"latitude": iot_data[42:50],
"longitude": iot_data[50:58],
"elevation": iot_data[58:62],
"speed": iot_data[62:66],
"direction": iot_data[66:70],
"time": iot_data[70:82],
"extention_id1": iot_data[82:84],
"extention_id1_data_length": iot_data[84:86],
"extention_id1_data": iot_data[86:94],
"extention_id2": iot_data[94:96],
"extention_id2_data_length": iot_data[96:98],
"extention_id2_data": iot_data[98:102],
"extention_id3": iot_data[102:104],
"extention_id3_data_length": iot_data[104:106],
"extention_id3_data": iot_data[106:110],
"check_code": iot_data[110:112],
"end_marker": iot_data[112:114]
}

for key, value in data.items():
    print(f"{key}: {value}")

def call_post_api(url, payload):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return response

url = "https://noealilrxxec8fe-astrodev.adb.ap-mumbai-1.oraclecloudapps.com/ords/procapps/iot/vehicle"

payload = {
        "device_ph_no": data["device_phone_no"],
        "iotfm_device_id": "",
        "iotfm_vehicle_id": "",
        "registration": "MH01CB1432",
        "error_msg": ""
    }

print(payload)

response = call_post_api(url, payload)
print(response)


