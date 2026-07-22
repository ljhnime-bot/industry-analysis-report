import os
import OpenDartReader
import pandas as pd

API_KEY = os.environ["DART_API_KEY"]
dart = OpenDartReader(API_KEY)
df = dart.finstate("336570", "2024", reprt_code="11011") # finstate returns standard IS, BS, CF
if df is not None:
    print(df.columns)
    print(df[['sj_nm', 'account_nm', 'ord']].head(15))
else:
    print("No data from finstate")
