from flask import Flask, render_template, jsonify
import serial
import threading
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

app = Flask(__name__)

# [공통 데이터 보관함]
latest_data = {
    "sea": 0.0, "lake": 0.0, "head": 0.0, 
    "waste": 0, "loss_cum": 0
}

# 1. 아두이노 연결 설정
ser = None
try:
    ser = serial.Serial('COM3', 9600, timeout=1)
    print("✅ [성공] 아두이노 포트 개방 완료")
except Exception as e:
    print(f"❌ [오류] 아두이노 연결 실패: {e}")

def read_arduino():
    global latest_data
    while True:
        if ser and ser.is_open:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    parts = line.split("|")
                    if len(parts) == 3:
                        latest_data["sea"] = float(parts[0])
                        latest_data["lake"] = float(parts[1])
                        latest_data["head"] = abs(float(parts[0]) - float(parts[1]))
                        latest_data["waste"] = int(parts[2])
                        latest_data["loss_cum"] += int(int(parts[2]) / 10)
            except Exception as e:
                pass
        time.sleep(0.1)

# 2. 수자원공사 API 호출 함수 (XML 파싱 포함)
def get_kwater_data():
    url = 'http://apis.data.go.kr/B500001/dam/sihwavalue/sihwaequip/sihwaequiplist'
    service_key = 'a8e1d37e6bc69ccac0b101c638f05e8a83ce096c866d4448f1c56ced78b6d28f' 
    
    # [1] 날짜 자동 설정
    from datetime import datetime, timedelta
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    yesterday_str = (now - timedelta(days=1)).strftime('%Y-%m-%d')

    params = {
        'serviceKey' : service_key, 
        'pageNo' : '1', 
        'numOfRows' : '24', 
        'stdt' : yesterday_str, 
        'eddt' : today_str, 
        '_type' : 'xml' 
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            sea_list, lake_list, time_list = [], [], []
            
            for item in root.findall('.//item'):
                s = item.findtext('seaRwl')
                l = item.findtext('lakeRwl')
                t = item.findtext('obsdt')
                if s and l:
                    sea_list.append(float(s))
                    lake_list.append(float(l))
                    time_list.append(t[-5:] if t else "") # 시간만 이쁘게 자르기 (예: 10:00)
# ... (중략: 데이터 append 하는 부분 이후)
            
            # [수정] 그래프는 왼쪽(과거) -> 오른쪽(최신)으로 가야 하므로 리스트를 뒤집습니다.
            sea_list.reverse()
            lake_list.reverse()
            time_list.reverse()

            if len(sea_list) > 0:
                print(f"✅ 데이터 순서 정렬 완료 (최신 데이터가 마지막으로)")
                return {'sea': sea_list, 'lake': lake_list, 'times': time_list}
            
            # [2] 중요: 데이터가 진짜로 들어왔는지 확인
            if len(sea_list) > 0:
                print(f"✅ 실시간 API 데이터 로드 성공 ({len(sea_list)}건)")
                return {'sea': sea_list, 'lake': lake_list, 'times': time_list}
            
        print("⚠️ 실시간 데이터가 아직 없습니다. 샘플 데이터를 표시합니다.")
    except Exception as e:
        print(f"⚠️ API 오류 발생: {e}. 샘플 데이터를 표시합니다.")
    
    # [3] 데이터가 없을 때 그래프를 살려낼 샘플 데이터 (방어막)
    return {
        'sea': [3.1, 3.5, 4.2, 3.8, 2.5, 1.1, -0.5, -1.5, -2.0, -1.8, -0.5, 1.2],
        'lake': [-1.2, -1.3, -1.5, -1.7, -1.9, -2.0, -1.8, -1.5, -1.2, -1.0, -0.8, -0.5],
        'times': ["00:00", "02:00", "04:00", "06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
    }

# 아두이노 쓰레드 시작
t = threading.Thread(target=read_arduino, daemon=True)
t.start()

# --- 라우팅 ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/data')
def get_data():
    return jsonify(latest_data)

@app.route('/weather')
def weather():
    api_result = get_kwater_data()
    # 아두이노 값과 API 값을 동시에 보냄
    return render_template('weather.html', 
                           api_data=api_result, 
                           arduino=latest_data)

@app.route('/simulator')
def simulator():
    return render_template('simulator.html')

@app.route('/history')
def history():
    return render_template('history.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)