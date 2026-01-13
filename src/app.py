from flask import Flask, render_template, jsonify
import serial
import threading
import time

app = Flask(__name__)

# 데이터 보관함
latest_data = {
    "sea": 0.0, "lake": 0.0, "head": 0.0, 
    "waste": 0, "loss_cum": 0
}

# [핵심] 아두이노 연결 시도
ser = None
try:
    # 포트 번호가 COM3가 맞는지 꼭 확인하세요!
    ser = serial.Serial('COM3', 9600, timeout=1)
    print("✅ [성공] 아두이노 포트 개방 완료")
except Exception as e:
    print(f"❌ [오류] 아두이노 연결 실패: {e}")

def read_arduino():
    global latest_data
    print("📡 [알림] 데이터 수집 쓰레드 시작됨")
    while True:
        if ser and ser.is_open:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"📥 수신 데이터: {line}") # 터미널에 데이터가 찍히는지 확인용
                    parts = line.split("|")
                    if len(parts) == 3:
                        latest_data["sea"] = float(parts[0])
                        latest_data["lake"] = float(parts[1])
                        latest_data["head"] = abs(float(parts[0]) - float(parts[1]))
                        latest_data["waste"] = int(parts[2])
                        latest_data["loss_cum"] += int(int(parts[2]) / 10)
            except Exception as e:
                print(f"⚠️ 데이터 해석 오류: {e}")
        time.sleep(0.1)

# 서버 시작 전 쓰레드 실행
t = threading.Thread(target=read_arduino, daemon=True)
t.start()

@app.route('/data')
def get_data():
    return jsonify(latest_data)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # use_reloader=False가 없으면 아두이노 연결이 두 번 시도되어 충돌납니다!
    app.run(debug=True, port=5000, use_reloader=False)