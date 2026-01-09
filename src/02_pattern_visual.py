import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr

# 1. 환경 설정 및 데이터 로드
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font='Malgun Gothic')

# 데이터 로드
df_p = pd.read_csv('data/rain_pattern_vs_waste.csv')
df_p['month'] = df_p['month'].astype(str)

metrics = [
    ('heavy_hours', '집중 강우 시간', 'skyblue'),
    ('rain_peak', '최대 시간 강수량', 'green'),
    ('rain_sum', '월 누적 강수량', 'blue'),
    ('top10_ratio', '강우 집중도', 'purple')
]

for idx, (col, label, color) in enumerate(metrics, 1):
    r, p = pearsonr(df_p[col], df_p['waste_sum'])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if col == 'heavy_hours':
        # [그림 1] 막대(강우시간) + 선(수거량)
        ax_twin = ax.twinx()
        bar = sns.barplot(data=df_p, x='month', y=col, ax=ax, color=color, alpha=0.6, label=f'막대: {label} (h)')
        line = sns.lineplot(data=df_p, x='month', y='waste_sum', ax=ax_twin, color='red', marker='o', linewidth=2, label='선: 쓰레기 수거량 (ton)')
        
        ax.set_ylabel(f'{label} (Hours)')
        ax_twin.set_ylabel('쓰레기 수거량 (ton)')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        
        # 범례를 하나로 합쳐서 상단 바깥에 표시
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax_twin.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)
    else:
        # [그림 2, 3, 4] 산점도 + 회귀선
        sns.regplot(data=df_p, x=col, y='waste_sum', ax=ax, color=color, 
                    line_kws={'color': 'orange', 'linestyle': '--', 'linewidth': 2},
                    label=f'점/선: {label} 대비 수거량 상관관계')
        ax.set_ylabel('쓰레기 수거량 (ton)')
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15))

    # 상관계수 수치 삽입 (텍스트 박스)
    stats_text = f'상관계수(r): {r:.3f}\n유의확률(p): {p:.3e}'
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    ax.set_title(f'[{idx}] {label} vs 쓰레기 수거량', fontsize=15, pad=35)
    ax.set_xlabel(f'{label} 수치')
    
    plt.tight_layout()
    plt.savefig(f'data/pattern_plot_labeled_{idx}_{col}.png', dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()