import os
import OpenDartReader
import pandas as pd

API_KEY = os.environ["DART_API_KEY"]
dart = OpenDartReader(API_KEY)
df = dart.finstate_all("336570", "2024", reprt_code="11011", fs_div="CFS")
bs = df[df['sj_div'] == 'BS'].copy()
bs['ord'] = pd.to_numeric(bs['ord'], errors='coerce')
bs = bs.sort_values('ord')
print(bs[['account_nm', 'ord']].to_string())
