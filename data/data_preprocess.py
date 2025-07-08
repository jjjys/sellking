import pandas as pd

# Read the Excel file, selecting columns by index (C=2, E=4, F=5, 0-based indexing)
file_path = r'C:\Users\user\Desktop\sellking\data\매도왕 상담 신청 (prod).xlsx'
df = pd.read_excel(file_path, sheet_name='시트1', usecols=[2, 4, 5])

# Remove rows where column C (index 2) is blank (NaN or empty)
df = df.dropna(subset=[df.columns[0]])

# Remove rows where both columns E and F (indices 4 and 5) are blank (NaN or empty)
df = df.dropna(subset=[df.columns[1], df.columns[2]], how='all')

# Remove duplicate rows, considering all selected columns
df = df.drop_duplicates()

# Save the processed DataFrame to a new Excel file
output_path = r'C:\Users\user\Desktop\sellking\data\adress_info.xlsx'
df.to_excel(output_path, index=False)