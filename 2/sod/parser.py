import pandas as pd

file_name = 'data.xlsx'
data = pd.read_excel(file_name, header=None)

for i in range(1, len(data.columns), 2):
    column = data.columns[i]
    values = data[i].dropna().head(20).tolist()

    if values:
        print(', '.join(map(str, values)))
