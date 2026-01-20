from flask import Flask, render_template, jsonify
import serial
import threading
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd
import os

app = Flask(__name__)

# --- [1] 과거 CSV 데이터 로드 로직 ---
csv_df = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# src 폴더 기준 상위 폴더의 data/sihwa_history.csv 접근
CSV_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "sihwa_history.csv"))

def init_csv():
    global csv_df
    if not os.path.exists(CSV_PATH):
        print(f"❌ [오류] CSV 파일을 찾을 수 없습니다: {CSV_PATH}")
        return

    try:
        # 한글 깨짐 방지를 위해 cp949 사용
        df = pd.read_csv(CSV_PATH, encoding="cp949")
        
        # '일자' 컬럼을 날짜 형식으로 변환 후 비교용/표시용 컬럼 생성
        df['일자'] = pd.to_datetime(df['일자'])
        df['date_only'] = df['일자'].dt.strftime('%Y-%m-%d')
        df['time_only'] = df['일자'].dt.strftime('%H:%M')
        
        csv_df = df
        print(f"✅ [성공] 과거 CSV 로드 완료 ({len(csv_df)} 행)")
    except Exception as e:
        print(f"❌ [오류] CSV 로드 중 에러 발생: {e}")

# 서버 시작 전 CSV 미리 로드
init_csv()

# --- [2] 실시간 아두이노 데이터 보관함 및 통신 ---
latest_data = {
    "sea": 0.0, "lake": 0.0, "head": 0.0, 
    "waste": 0, "loss_cum": 0
}

ser = None
try:
    ser = serial.Serial('COM3', 9600, timeout=1)
    print("✅ [성공] 아두이노 포트(COM3) 개방 완료")
except Exception as e:
    print(f"⚠️ [주의] 아두이노 연결 실패(시뮬레이터 모드): {e}")

def read_arduino():
    global latest_data
    while True:
        if ser and ser.is_open:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    parts = line.split("|")
                    if len(parts) == 3:
                        sea = float(parts[0])
                        lake = float(parts[1])
                        latest_data["sea"] = sea
                        latest_data["lake"] = lake
                        latest_data["head"] = abs(sea - lake)
                        latest_data["waste"] = int(parts[2])
                        latest_data["loss_cum"] += int(int(parts[2]) / 10)
            except:
                pass
        time.sleep(0.1)

# 아두이노 읽기 쓰레드 시작
t = threading.Thread(target=read_arduino, daemon=True)
t.start()

# --- [3] K-water API 호출 함수 ---
def get_kwater_data():
    url = 'http://apis.data.go.kr/B500001/dam/sihwavalue/sihwaequip/sihwaequiplist'
    service_key = 'a8e1d37e6bc69ccac0b101c638f05e8a83ce096c866d4448f1c56ced78b6d28f' 
    
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
                    time_list.append(t[-5:] if t else "") 
            
            # 그래프 방향 정렬 (과거 -> 현재)
            sea_list.reverse()
            lake_list.reverse()
            time_list.reverse()

            if len(sea_list) > 0:
                return {'sea': sea_list, 'lake': lake_list, 'times': time_list}
    except Exception as e:
        print(f"⚠️ API 오류: {e}")
    
    # API 실패 시 샘플 데이터
    return {
        'sea': [3.1, 3.5, 4.2, 3.8, 2.5, 1.1, -0.5, -1.5, -2.0, -1.8, -0.5, 1.2],
        'lake': [-1.2, -1.3, -1.5, -1.7, -1.9, -2.0, -1.8, -1.5, -1.2, -1.0, -0.8, -0.5],
        'times': ["00:00", "02:00", "04:00", "06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
    }

# --- [4] 라우팅 (URL 연결) ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/weather')
def weather():
    # 첫 로딩 시 실시간 데이터를 가져와 전달
    api_result = get_kwater_data()
    return render_template('weather.html', api_data=api_result, arduino=latest_data)

@app.route('/data')
def get_arduino_data():
    return jsonify(latest_data)

@app.route('/api/realtime')
def get_realtime_api():
    return jsonify(get_kwater_data())

@app.route('/api/history/<target_date>')
def get_history_api(target_date):
    global csv_df
    if csv_df is None:
        return jsonify({'error': 'CSV 데이터가 로드되지 않았습니다.'}), 500

    result = csv_df[csv_df['date_only'] == target_date]
    if result.empty:
        return jsonify({'sea': [], 'lake': [], 'times': []})

    return jsonify({
        'sea': result['해수위(EL.m)'].tolist(),
        'lake': result['호수위(EL.m)'].tolist(),
        'times': result['time_only'].tolist()
    })

@app.route('/simulator')
def simulator():
    return render_template('simulator.html')

@app.route('/history')
def history_page():
    return render_template('history.html')

if __name__ == '__main__':
    # use_reloader=False는 아두이노 쓰레드 중복 실행 방지용
    app.run(debug=True, port=5000, use_reloader=False)