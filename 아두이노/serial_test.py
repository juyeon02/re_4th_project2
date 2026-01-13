import serial
import time

# 본인의 아두이노 포트 번호로 수정 (예: 'COM3')
py_serial = serial.Serial(port='COM3', baudrate=9600)

while True:
    if py_serial.readable():
        response = py_serial.readline().decode()
        data = response.replace('\r\n', '').split('|')
        
        if len(data) == 2:
            head = data[0]
            waste = data[1]
            print(f"🌊 현재 낙차: {head}cm | 🗑️ 쓰레기 강도: {waste}")