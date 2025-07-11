import pandas as pd

file_path = r'C:\Users\user\Desktop\sellking\data\매도왕 상담 신청 (prod).xlsx'
df = pd.read_excel(file_path, sheet_name='시트1', usecols=[2, 4, 5])

# 첫 번째 컬럼(인덱스 0)이 공백 문자열이 아니고 NaN이 아닌 행만 유지
df = df[df[df.columns[0]].notna() & df[df.columns[0]].str.strip().ne('')]

# 두 번째와 세 번째 컬럼(인덱스 1, 2)이 모두 NaN인 행 제거
df = df.dropna(subset=[df.columns[1], df.columns[2]], how='all')

# 중복된 행 제거
df = df.drop_duplicates()

output_path = r'C:\Users\user\Desktop\sellking\data\adress_info.xlsx'
df.to_excel(output_path, index=False)