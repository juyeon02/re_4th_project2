import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 환경 설정 및 데이터 로드
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
df = pd.read_csv('data/power_rain_merged_2024.csv')
df['날짜'] = pd.to_datetime(df['날짜'])

# 2. 기준 효율 및 손실 계산 로직
baseline_by_head = {
    1.0: 28031.8, 1.5: 27965.5, 2.0: 29206.2, 2.5: 29979.2, 
    3.0: 30260.5, 3.5: 31356.2, 4.0: 31609.8, 4.5: 31356.3,
    5.0: 31438.4, 5.5: 33196.7, 6.0: 34972.5, 6.5: 33796.0,
    7.0: 32895.8, 7.5: 28701.5, 8.0: 27065.4
}
global_baseline = 30844.9
SMP = 150 
CLEAN_COST = 5_000_000 

def calc_loss_won(row):
    head_key = round(row['낙차'] * 2) / 2
    eff = baseline_by_head.get(head_key, global_baseline)
    expected_power = eff * row['낙차']
    loss_kwh = expected_power - row['합계(킬로와트시)']
    return max(0, loss_kwh) * SMP

df['loss_won'] = df.apply(calc_loss_won, axis=1)

# ---------------------------------------------------------
# 보완 ①: "대표 이벤트" 필터링 (괄호 오류 수정 완료)
# ---------------------------------------------------------
max_rain_idx = df['평균강수량(mm)'].idxmax()
max_rain_date = df.loc[max_rain_idx, '날짜']
event_start = max_rain_date - pd.Timedelta(hours=24)
event_end = max_rain_date + pd.Timedelta(hours=48)

# 조건을 각각 ( )로 감싸서 bitwise_and 오류를 방지합니다.
sample_df = df[(df['날짜'] >= event_start) & (df['날짜'] <= event_end)].copy()

# ---------------------------------------------------------
# 보완 ②: 누적 손실액 계산
# ---------------------------------------------------------
sample_df['cum_loss_won'] = sample_df['loss_won'].cumsum()

# 3. 시각화
fig, ax1 = plt.subplots(figsize=(14, 7))
ax2 = ax1.twinx()

# X축 라벨 가독성 (월-일 시)
x_labels = sample_df['날짜'].dt.strftime('%m-%d %H')

# (1) 강수량 - 막대
sns.barplot(x=x_labels, y=sample_df['평균강수량(mm)'], ax=ax1, color='blue', alpha=0.2, label='시간당 강수량(mm)')

# (2) 시간당 손실액 - 빨간 점선
sns.lineplot(x=x_labels, y=sample_df['loss_won'], ax=ax2, color='red', marker='o', alpha=0.4, label='순간 손실액(원)')

# (3) 누적 손실액 - 진한 빨간 실선
sns.lineplot(x=x_labels, y=sample_df['cum_loss_won'], ax=ax2, color='darkred', linewidth=3, label='누적 발전 손실액(원)')

# (4) 수거 비용 기준선 (Threshold)
ax2.axhline(CLEAN_COST, color='black', linestyle=':', linewidth=3, label=f'수거 비용 기준선 ({CLEAN_COST/10000:.0f}만원)')

ax1.set_title(f'강우 이벤트에 따른 경제적 수거 적기 분석 (최대 강우일: {max_rain_date.date()})', fontsize=16, pad=20)
ax1.set_xlabel('시간 (월-일 시)')
ax1.set_ylabel('강수량 (mm)')
ax2.set_ylabel('손실 금액 (원)')
ax1.tick_params(axis='x', rotation=45)

# 범례 통합
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.tight_layout()
plt.show()