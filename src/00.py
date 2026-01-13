import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 환경 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로드
# 시간별 발전 데이터
df_gen = pd.read_csv('data/power_2024_hourly.csv', encoding='utf-8-sig') 
# 시간별 강수량 데이터 (컬럼명: 일시, 평균강수량(mm))
df_rain = pd.read_csv('data/rain_hourly_2024_avg.csv') 

# 3. 날짜 형식 통일 및 데이터 병합
df_gen['날짜'] = pd.to_datetime(df_gen['날짜'])
df_rain['일시'] = pd.to_datetime(df_rain['일시'])

# '날짜'와 '일시'를 기준으로 병합하여 강수량 정보를 발전 데이터에 붙임
df = pd.merge(df_gen, df_rain, left_on='날짜', right_on='일시', how='inner')

# 4. 효율 계산 및 데이터 정제
df['낙차'] = df['해수위(ELm)'] - df['호수위(ELm)']
df['efficiency'] = df['합계(킬로와트시)'] / df['낙차']

# 유효 데이터 필터링 (낙차 1.0m 이상)
df = df[(df['낙차'] >= 1.0) & (df['합계(킬로와트시)'] > 0)].copy()

# 5. 시차(Time Lag) 반영 및 상태 정의
# 비 온 뒤 3시간 후에 쓰레기가 유도된다는 상관분석 결과 반영
df['after_rain_3h'] = df['평균강수량(mm)'].shift(3) > 0

df['status'] = '맑음'
df.loc[df['after_rain_3h'] == True, 'status'] = '비 온 후(쓰레기유입)'

# 6. 낙차 구간별(Head Group) 효율 비교
df['head_group'] = (df['낙차'] // 0.5) * 0.5
comparison = df.groupby(['head_group', 'status'])['efficiency'].mean().unstack()

# 결과가 있는 구간에 대해 효율 감소율 계산
if '비 온 후(쓰레기유입)' in comparison.columns and '맑음' in comparison.columns:
    comparison['효율감소율(%)'] = (comparison['맑음'] - comparison['비 온 후(쓰레기유입)']) / comparison['맑음'] * 100
    print("=== 📊 [분석결과] 낙차 조건을 통제한 실시간 쓰레기 페널티 ===")
    print(comparison.dropna())

    # 7. 시각화
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df, x='head_group', y='efficiency', hue='status', 
                 hue_order=['맑음', '비 온 후(쓰레기유입)'], marker='o')
    plt.title('낙차 구간별 쓰레기 유입에 따른 실제 효율 저하 (이전 분석 결과 반영)', fontsize=15)
    plt.xlabel('낙차 구간 (m)')
    plt.ylabel('평균 발전 효율 (kWh/m)')
    plt.grid(True, alpha=0.3)
    plt.show()
else:
    print("⚠️ 비교할 수 있는 강우 후 데이터가 부족합니다.")