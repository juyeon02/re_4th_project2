import pandas as pd

# 조력 데이터, 평균강수량 데이터 읽어오기
power = pd.read_csv('data/sihwa_tidal.csv', encoding='utf-8')
rain = pd.read_csv('data/rain_avg.csv')

# 시간컬럼 수정
power['시간'] = power['시간'].str.replace('24:00', '00:00')
rain['일시'] = pd.to_datetime(rain['일시'])

# 조력 데이터의 시간 형식 합치기 ('날짜' + '시간' -> '일시')
power['일시'] = pd.to_datetime(power['날짜'] + ' ' + power['시간'])


# '일시' 기준으로 데이터 합치기
final_data= pd.merge(power,rain, on= '일시')

# '낙차' 계산
final_data['낙차'] = final_data['해수위(ELm)'] - final_data['호수위(ELm)'] 

final_data.to_csv('data/final_merged.csv', index=False, encoding='utf-8-sig')

print(f'전체 데이터 개수:{len(final_data)}개')
print(final_data[['일시', '합계(킬로와트시)', '평균강수량(mm)', '낙차']].head())