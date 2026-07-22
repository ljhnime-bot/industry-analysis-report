import os
import OpenDartReader
import pandas as pd

API_KEY = os.environ["DART_API_KEY"]
dart = OpenDartReader(API_KEY)
df = dart.finstate_all("336570", "2024", reprt_code="11011", fs_div="CFS")
print(df.columns)
if 'ord' in df.columns:
    print(df[['account_nm', 'ord']].head(10))
else:
    print(df[['account_nm']].head(10))
