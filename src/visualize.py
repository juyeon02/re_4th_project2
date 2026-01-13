import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import platform

# 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


df = pd.read_csv('data/final_merged.csv')

# 발전 중인 데이터만 추출
# 조건1 :  발전량 존재
# 조건2 : 사양서 기준 최소 가동 낙차 1.00m 이상
condition = (df['합계(킬로와트시)'] > 0) & (df['낙차'] >= 1.00)
df_active = df[condition].copy()

# 효율 지표 계산 : 낙차 1m당 생산량
df_active['효율'] = df_active['합계(킬로와트시)']/ df_active['낙차']

# 4. 시각화 (이상치를 포함한 전체 분포 확인)
plt.figure(figsize=(10, 6))
sns.boxplot(x=(df_active['평균강수량(mm)'] > 10), y='효율', data=df_active)

plt.title('Power Efficiency (Min. Head >= 1.00m, Raw Outliers Included)')
plt.xticks([0, 1], ['No Rain (False)', 'Rain (True)'])
plt.ylabel('Efficiency (kWh/m)')
plt.show()

# 5. 평균값 확인 (이상치가 평균에 미치는 영향 포함)
avg_no = df_active[df_active['평균강수량(mm)'] == 0]['효율'].mean()
avg_yes = df_active[df_active['평균강수량(mm)'] > 0]['효율'].mean()

print(f"--- 분석 결과 (사양 기준 1.00m 적용 / 이상치 포함) ---")
print(f"비 안 올 때 평균 효율: {avg_no:.2f} kWh/m")
print(f"비 올 때 평균 효율: {avg_yes:.2f} kWh/m")
if avg_no > 0:
    print(f"효율 감소율: {((avg_no - avg_yes) / avg_no * 100):.2f}%")