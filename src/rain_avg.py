# 강수량 평균
import pandas as pd

# 원본 강수량 파일 읽기
df = pd.read_csv('data/rainfall_data.csv' , encoding='cp949')

# '일시' 컬럼을 컴퓨터가 인식하는 시간 형식으로 바꾸기
df['일시'] = pd.to_datetime(df['일시'])

# 시간대별 6개 지점의 강수량 평균 
avg_result = df.groupby('일시')['강수량(mm)'].mean().reset_index()

# 컬럼 명 변경
avg_result.columns = ['일시', '평균강수량(mm)']

# 새로운 파일로 저장
avg_result.to_csv('data/rain_avg.csv', index=False , encoding='utf-8-sig')

print('성공')
print(avg_result.head())

