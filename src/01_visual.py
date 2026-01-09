import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# 1. 한글 폰트 및 스타일 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font='Malgun Gothic')

# 2. 데이터 로드 및 전처리
df_env = pd.read_csv('data/rain_waste_monthly_2020_2024_merged.csv')
df_env['date'] = pd.to_datetime(df_env['date']).dt.to_period('M').astype(str)

try:
    df_gen_raw = pd.read_csv('raw_data/power_2024_hourly.csv', encoding='utf-8-sig')
except UnicodeDecodeError:
    df_gen_raw = pd.read_csv('raw_data/power_2024_hourly.csv', encoding='cp949')

df_gen_raw['날짜'] = pd.to_datetime(df_gen_raw['날짜'])
df_gen_raw['낙차'] = df_gen_raw['해수위(ELm)'] - df_gen_raw['호수위(ELm)']
df_gen_valid = df_gen_raw[(df_gen_raw['낙차'] >= 1.0) & (df_gen_raw['합계(킬로와트시)'] > 0)].copy()
df_gen_valid['효율'] = df_gen_valid['합계(킬로와트시)'] / df_gen_valid['낙차']

df_gen_monthly = df_gen_valid.groupby(df_gen_valid['날짜'].dt.to_period('M'))['효율'].mean().reset_index()
df_gen_monthly.columns = ['date', 'avg_efficiency']
df_gen_monthly['date'] = df_gen_monthly['date'].astype(str)

df_final = pd.merge(df_env, df_gen_monthly, on='date', how='left')

# --- 그래프 1: 강수량 vs 쓰레기 상관관계 ---
plt.figure(figsize=(10, 6))
correlation, p_value = stats.pearsonr(df_final['rain_avg'], df_final['waste_sum'])
sns.regplot(x='rain_avg', y='waste_sum', data=df_final, 
            scatter_kws={'alpha':0.6}, line_kws={'color':'red', 'label':f'r={correlation:.4f}'})
plt.title(f'강수량과 쓰레기 수거량 상관분석 (p-value: {p_value:.2e})', fontsize=14)
plt.xlabel('월평균 강수량 (mm)')
plt.ylabel('쓰레기 수거량 (ton)')
plt.legend()
plt.savefig('data/correlation_analysis.png', dpi=300)
plt.show()

# --- 그래프 2: 월별 추이 변화 (이중축) ---
fig, ax1 = plt.subplots(figsize=(12, 6))
ax2 = ax1.twinx()
ax1.bar(df_final['date'], df_final['rain_avg'], color='skyblue', alpha=0.5, label='강수량(mm)')
ax2.plot(df_final['date'], df_final['waste_sum'], color='green', marker='o', label='쓰레기(ton)')
plt.title('월별 강수량 및 쓰레기 수거량 추이 (2020-2024)', fontsize=14)
ax1.set_xticks(df_final['date'][::6]) 
plt.setp(ax1.get_xticklabels(), rotation=45)
ax1.set_ylabel('강수량 (mm)', color='blue')
ax2.set_ylabel('쓰레기 (ton)', color='green')
plt.savefig('data/monthly_trends.png', dpi=300)
plt.show()

# --- 그래프 3: 머신러닝 중요도 ---
plt.figure(figsize=(10, 5))
importance_data = {
    'Feature': ['낙차(물리)', '강수량(환경)', '쓰레기(환경)'],
    'Importance': [0.8080, 0.1018, 0.0902]
}
df_imp = pd.DataFrame(importance_data)
sns.barplot(x='Importance', y='Feature', data=df_imp, palette='magma')
plt.title('발전 효율 결정 요인 중요도 분석', fontsize=14)
plt.xlim(0, 1)
for i, v in enumerate(df_imp['Importance']):
    plt.text(v + 0.01, i, f'{v*100:.1f}%', va='center', fontweight='bold')
plt.savefig('data/feature_importance.png', dpi=300)
plt.show()

print("✅ 모든 그래프가 개별 저장되었습니다: correlation_analysis.png, monthly_trends.png, feature_importance.png")