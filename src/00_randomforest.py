import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# 1. 월별 환경 데이터 로드 (2024년만 추출)
df_env = pd.read_csv('data/rain_waste_monthly_2020_2024_merged.csv')
df_env['date'] = pd.to_datetime(df_env['date']).dt.to_period('M')
df_env_2024 = df_env[df_env['date'].dt.year == 2024].copy()

# 2. 시간별 발전 데이터 로드
df_gen = pd.read_csv('data/power_2024_hourly.csv', encoding='utf-8-sig') 
df_gen['날짜'] = pd.to_datetime(df_gen['날짜'])
df_gen['YM'] = df_gen['날짜'].dt.to_period('M')

# 3. 데이터 병합 (시간 데이터 옆에 월 환경 수치 붙이기)
# 시간별 데이터(8760행)에 월별 환경 수치가 각 행마다 반복해서 들어갑니다.
df_train = pd.merge(df_gen, df_env_2024, left_on='YM', right_on='date', how='inner')

# 4. 특성 생성: 낙차 및 타겟 설정
df_train['낙차'] = df_train['해수위(ELm)'] - df_train['호수위(ELm)']
# 낙차가 있고 발전이 일어난 데이터만 학습에 사용 (데이터 정제)
df_train = df_train[(df_train['낙차'] > 0) & (df_train['합계(킬로와트시)'] > 0)].copy()
df_train['효율'] = df_train['합계(킬로와트시)'] / df_train['낙차']

# 5. 모델 학습 (랜덤 포레스트)
# 원인: 낙차(조력 핵심), 강수량, 쓰레기양
X = df_train[['낙차', 'rain_avg', 'waste_sum']]
y = df_train['효율']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 6. 중요도 분석 (어떤게 효율에 가장 큰 영향을 주나?)
importances = model.feature_importances_
print("=== 🤖 환경 변수 영향력(중요도) 분석 ===")
for name, val in zip(X.columns, importances):
    print(f"{name}: {val:.4f}")