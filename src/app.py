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

# 시화조력 실제 제원 기반 상수
RHO = 1025      # 해수 밀도 (kg/m3)
G = 9.81        # 중력 가속도 (m/s2)
ETA = 0.90      # 수차 및 발전기 종합 효율
Q_MAX = 482     # 수차 1기당 최대 설계 유량 (m3/s)

def get_performance_data(head, waste):
    # 1. 가용 유량 계산 (쓰레기 수치 0~1023에 따라 최대 40% 감소 가정)
    # 실제 환경에서는 Trash Rack의 차압(Differential Pressure)으로 계산하지만, 
    # 여기서는 센서값(waste)을 유량 저하 요인으로 매핑합니다.
    blockage_ratio = (waste / 1023) * 0.4 
    current_q = Q_MAX * (1 - blockage_ratio)
    
    # 2. 발전 출력 계산 (P = η * ρ * g * Q * H)
    # 단위를 MW로 변환하기 위해 1,000,000으로 나눔
    theoretical_p = (ETA * RHO * G * Q_MAX * head) / 1000000  # 쓰레기 없을 때
    actual_p = (ETA * RHO * G * current_q * head) / 1000000    # 현재 상태
    
    # 낙차가 너무 낮으면(2m 미만) 발전 불가
    if head < 2.0:
        theoretical_p, actual_p = 0, 0

    return {
        "theoretical_p": round(theoretical_p, 2),
        "actual_p": round(actual_p, 2),
        "efficiency": round((actual_p / theoretical_p * 100), 1) if theoretical_p > 0 else 0,
        "loss_mw": round(theoretical_p - actual_p, 2)
    }

# 서버 시작 전 쓰레드 실행
t = threading.Thread(target=read_arduino, daemon=True)
t.start()

@app.route('/data')
def get_data():
    return jsonify(latest_data)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/simulator')
def simulator():
    return render_template('simulator.html')

@app.route('/weather')
def weather():
    return render_template('weather.html')

@app.route('/history')
def history():
    return render_template('history.html')

if __name__ == '__main__':
    # use_reloader=False가 없으면 아두이노 연결이 두 번 시도되어 충돌납니다!
    app.run(debug=True, port=5000, use_reloader=False)