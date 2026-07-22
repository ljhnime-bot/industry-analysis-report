import os
import OpenDartReader
import pandas as pd
import concurrent.futures

def fetch_financial_statements(api_key, company_code, year, reprt_code='11011'):
    """
    DART API를 통해 기업의 전체 재무제표(BS, PL, CF)를 가져오는 함수
    
    :param api_key: DART Open API Key
    :param company_code: 종목코드 (예: '005930') 또는 기업명
    :param year: 사업연도 (예: '2023')
    :param reprt_code: 보고서 코드 (11011: 사업보고서)
    :return: bs_df(재무상태표), pl_df(손익계산서), cf_df(현금흐름표) DataFrame 튜플
    """
    try:
        dart = OpenDartReader(api_key)
        
        # fnlttSinglAcntAll API를 호출하여 전체 재무제표 가져오기
        # fs_div='CFS'는 연결재무제표, 'OFS'는 별도(개별)재무제표
        df_all = dart.finstate_all(company_code, year, reprt_code=reprt_code, fs_div='CFS')
        
        if df_all is None or df_all.empty:
            print(f"[{company_code}] 해당 연도({year})의 재무제표 데이터를 찾을 수 없습니다.")
            return None, None, None

        # 금액 컬럼 전처리 (문자열 -> 숫자 변환, 없는 값은 0 처리)
        for col in ['thstrm_amount', 'frmtrm_amount']:
            if col in df_all.columns:
                df_all[col] = pd.to_numeric(df_all[col].str.replace(',', ''), errors='coerce').fillna(0)

        # 재무제표 종류별로 분리하고, 어느 연도 데이터인지 'year' 컬럼 추가
        bs_df = df_all[df_all['sj_div'] == 'BS'].copy()
        pl_df = df_all[df_all['sj_div'].isin(['IS', 'CIS'])].copy()
        cf_df = df_all[df_all['sj_div'] == 'CF'].copy()
        
        bs_df.insert(0, 'year', year)
        pl_df.insert(0, 'year', year)
        cf_df.insert(0, 'year', year)
        
        return bs_df, pl_df, cf_df
        
    except Exception as e:
        print(f"[{year}년] 데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None, None, None

if __name__ == "__main__":
    # =================================================================
    # [필수] 발급받은 DART API Key
    # =================================================================
    API_KEY = os.environ["DART_API_KEY"]  # 환경변수로 설정: set DART_API_KEY=...
    
    COMPANY = "336570"  # 원텍 종목코드
    
    # 가져오고 싶은 연도를 리스트로 지정 (예: 2021년부터 2025년)
    YEARS = ["2021", "2022", "2023", "2024", "2025"]
    
    print(f"'{COMPANY}'의 {YEARS}년도 연결재무제표 다운로드를 병렬로 시작합니다...\n")
    
    all_bs = []
    all_pl = []
    all_cf = []
    
    # ThreadPoolExecutor를 사용해 여러 연도의 데이터를 동시에(병렬로) 가져오기
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # 각 연도별로 함수 실행 예약
        future_to_year = {executor.submit(fetch_financial_statements, API_KEY, COMPANY, y): y for y in YEARS}
        
        # 완료되는 순서대로 결과 받기
        for future in concurrent.futures.as_completed(future_to_year):
            y = future_to_year[future]
            try:
                bs, pl, cf = future.result()
                if bs is not None:
                    all_bs.append(bs)
                    all_pl.append(pl)
                    all_cf.append(cf)
                    print(f"[{y}년] 데이터 다운로드 완료!")
            except Exception as exc:
                print(f"[{y}년] 처리 중 예외 발생: {exc}")

    # 데이터가 정상적으로 수집되었다면 엑셀 파일로 저장
    if all_bs:
        final_bs = pd.concat(all_bs, ignore_index=True)
        final_pl = pd.concat(all_pl, ignore_index=True)
        final_cf = pd.concat(all_cf, ignore_index=True)
        
        # 이미지로 보는 재무제표처럼 (행: 계정과목, 열: 연도) 피벗 테이블 만들기
        def make_pretty_table(df, sj_div):
            if df.empty: return df
            # 중복 제거
            df = df.drop_duplicates(subset=['year', 'account_nm'], keep='first')
            
            # 행은 계정명, 열은 연도로 구성 (값은 당기금액)
            pivot_df = df.pivot(index='account_nm', columns='year', values='thstrm_amount')
            
            # 재무제표 원본 순서(ord) 유지 (가장 최신 연도 기준)
            max_year = df['year'].max()
            order_mapping = df[df['year'] == max_year].set_index('account_nm')['ord']
            order_mapping = pd.to_numeric(order_mapping, errors='coerce').fillna(9999)
            
            # 계정과목을 예쁘게 정렬하기 위한 커스텀 정렬 로직
            def custom_sort(account_nm):
                orig_ord = order_mapping.get(account_nm, 9999)
                if sj_div == 'BS':
                    name_str = str(account_nm).replace(" ", "")
                    # 1. 대분류 그룹핑 (자산, 부채, 자본)
                    if '자본과부채' in name_str or '부채와자본' in name_str:
                        group = 4
                    elif '자본' in name_str and '부채' not in name_str:
                        group = 3
                    elif '부채' in name_str and '자본' not in name_str:
                        group = 2
                    elif '자산' in name_str and '부채' not in name_str and '자본' not in name_str:
                        group = 1
                    else:
                        group = 5
                    
                    # 2. '총계'는 해당 그룹의 제일 아래로 이동
                    is_total = 1 if '총계' in name_str else 0
                    
                    # 그룹 -> 총계여부 -> 원래순서 순으로 정렬
                    return (group, is_total, orig_ord)
                else:
                    # PL, CF는 기본 DART 순서 유지
                    return (1, 0, orig_ord)

            pivot_df['sort_key'] = [custom_sort(x) for x in pivot_df.index]
            pivot_df = pivot_df.sort_values(by='sort_key').drop(columns=['sort_key'])
            
            # 최신 연도가 왼쪽으로 오도록 정렬 (예: 2025, 2024, 2023)
            cols = sorted(pivot_df.columns, reverse=True)
            pivot_df = pivot_df[cols]
            
            # 숫자에 콤마(,) 찍기 및 0은 '-'로 표시
            for col in pivot_df.columns:
                pivot_df[col] = pivot_df[col].apply(
                    lambda x: f"{int(x):,}" if pd.notnull(x) and x != 0 else "-"
                )
            
            pivot_df.index.name = None # 인덱스 이름 숨기기
            return pivot_df

        pretty_bs = make_pretty_table(final_bs, 'BS')
        pretty_pl = make_pretty_table(final_pl, 'PL')
        pretty_cf = make_pretty_table(final_cf, 'CF')
        
        # 엑셀 파일 생성
        excel_filename = f"{COMPANY}_다년간_재무제표.xlsx"
        
        print(f"\n엑셀 파일({excel_filename})에 데이터를 저장하는 중...")
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            pretty_bs.to_excel(writer, sheet_name='재무상태표(BS)')
            pretty_pl.to_excel(writer, sheet_name='손익계산서(PL)')
            pretty_cf.to_excel(writer, sheet_name='현금흐름표(CF)')
            
        print(f"저장 완료! 같은 폴더에서 '{excel_filename}' 파일을 확인해 보세요.")
    else:
        print("\n수집된 데이터가 없어서 엑셀 파일을 만들지 못했습니다.")
