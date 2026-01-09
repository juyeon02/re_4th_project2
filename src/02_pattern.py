import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# 1. 데이터 로드
# 시간별 강수량 데이터 (컬럼명: 일시, 평균강수량(mm))
df_rain = pd.read_csv('data/rain_hourly_2024_avg.csv')
df_rain['일시'] = pd.to_datetime(df_rain['일시'])

# 월별 쓰레기 데이터 (컬럼명: date, waste_sum)
df_waste = pd.read_csv('data/rain_waste_monthly_2020_2024_merged.csv')
df_waste['date'] = pd.to_datetime(df_waste['date']).dt.to_period('M')

# 2. 강우 패턴 지표 계산 (월 단위 요약)
df_rain['month'] = df_rain['일시'].dt.to_period('M')

def top10_ratio(x):
    if x.sum() == 0: return 0
    threshold = np.percentile(x, 90)
    return x[x >= threshold].sum() / x.sum()

# 월별로 묶어서 패턴 변수 생성
monthly_rain = df_rain.groupby('month')['평균강수량(mm)'].agg(
    rain_sum='sum',    # 월 누적 강수량
    rain_peak='max',   # 월 최대 시간 강수량
).reset_index()

# 집중 강우 시간 수 (10mm/h 이상)
heavy_hours = df_rain[df_rain['평균강수량(mm)'] >= 10].groupby('month')['평균강수량(mm)'].count().reset_index()
heavy_hours.columns = ['month', 'heavy_hours']

# 상위 10% 집중도
top10 = df_rain.groupby('month')['평균강수량(mm)'].apply(top10_ratio).reset_index()
top10.columns = ['month', 'top10_ratio']

# 3. 데이터 통합
monthly = pd.merge(monthly_rain, heavy_hours, on='month', how='left').fillna(0)
monthly = pd.merge(monthly, top10, on='month', how='left')
# 쓰레기 데이터와 최종 병합
final_pattern = pd.merge(monthly, df_waste[['date', 'waste_sum']], left_on='month', right_on='date', how='inner')

# 4. 패턴 vs 쓰레기 상관분석 실행
print("=== 📊 강우 패턴 vs 쓰레기 유입 상관분석 결과 ===")
metrics = ['rain_sum', 'rain_peak', 'heavy_hours', 'top10_ratio']
for col in metrics:
    r, p = pearsonr(final_pattern[col], final_pattern['waste_sum'])
    print(f"[{col}] r = {r:.3f}, p-value = {p:.3e}")

# 5. 결과 저장 (나중에 웹사이트에서 쓸 용도)
final_pattern.to_csv('data/rain_pattern_vs_waste.csv', index=False, encoding='utf-8-sig')