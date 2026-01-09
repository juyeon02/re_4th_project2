import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 환경 설정 및 데이터 로드
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 앞서 병합했던 통합 데이터(발전+강수) 로드
# df_train에 '낙차', '평균강수량(mm)', '합계(킬로와트시)'가 있다고 가정
df = pd.read_csv('data/power_rain_merged_2024.csv') 

# 2. 기준선 산출을 위한 '정상(Clean) 데이터' 추출
# 사용자님의 조건: 무강우 + 발전 중 + 낙차 발생
df_base = df[
    (df['평균강수량(mm)'] <= 0.5) & 
    (df['낙차'] > 1) & 
    (df['합계(킬로와트시)'] > 0)
].copy()

# 3. 기준 효율 계산
df_base['효율'] = df_base['합계(킬로와트시)'] / df_base['낙차']
global_baseline = df_base['효율'].mean()

# [고도화] 낙차 구간별 기준 효율 (낙차 중요도 80% 반영)
df_base['head_group'] = (df_base['낙차'] // 0.5) * 0.5
group_baseline = df_base.groupby('head_group')['효율'].mean()

print(f"📏 전체 평균 기준 효율: {global_baseline:.3f} kWh/m")
print("\n📊 낙차 구간별 세부 기준 효율:")
print(group_baseline)

# 4. 시각화 (기준선 확인)
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_base, x='낙차', y='효율', alpha=0.3, color='gray', label='정상상태 개별 데이터')
sns.lineplot(x=group_baseline.index, y=group_baseline.values, color='red', marker='o', linewidth=3, label='기준선 (Baseline)')

# 수치 표시
plt.axhline(global_baseline, color='blue', linestyle='--', label=f'전체평균: {global_baseline:.1f}')
ax.set_title('발전 효율 기준선(Baseline) 설정 결과', fontsize=15, pad=20)
ax.set_xlabel('낙차 (m)')
ax.set_ylabel('발전 효율 (kWh/m)')
ax.legend(loc='upper right')

plt.tight_layout()
plt.savefig('data/efficiency_baseline.png', dpi=300)
plt.show()