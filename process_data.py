import os
import glob
import json
import pandas as pd

def get_latest_excel():
    """downloads 폴더 및 현재 폴더에서 가장 최신 엑셀 파일 자동 탐색"""
    search_patterns = [
        os.path.join("downloads", "*.xlsx"),
        os.path.join("downloads", "*.xls"),
        "*.xlsx",
        "*.xls"
    ]
    
    files = []
    for pattern in search_patterns:
        files.extend(glob.glob(pattern))
        
    if not files:
        return None
    
    # 가장 최근에 수정/생성된 파일 선택
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def process_atis_excel():
    print("=" * 50)
    print("🚀 [1단계] 엑셀 파일 탐색 시작")
    
    excel_path = get_latest_excel()
    if not excel_path:
        print("❌ [오류] 폴더 내에서 엑셀 파일(.xlsx, .xls)을 찾을 수 없습니다!")
        print("    downloads 폴더에 엑셀 파일이 잘 들어있는지 확인해 주세요.")
        print("=" * 50)
        return

    print(f"✅ [발견] 읽어올 파일: {excel_path}")
    print("=" * 50)
    print("⚙️ [2단계] 데이터 파싱 시작")

    try:
        # ATIS 엑셀 원본은 2번째 줄(header=1)이 데이터 제목입니다.
        df = pd.read_excel(excel_path, header=1)
        
        # 유효한 컬럼 추출 ('비고' 및 Unnamed 제외)
        raw_headers = [
            str(col).strip() for col in df.columns 
            if '비고' not in str(col) and not str(col).startswith('Unnamed')
        ]
        headers = raw_headers + ['상세 제원']

        rows = []
        for idx, row in df.iterrows():
            row_data = {}
            has_data = False
            
            for col in raw_headers:
                val = row[col]
                if pd.isna(val) or str(val).strip() in ['', '-', 'nan']:
                    row_data[col] = '-'
                else:
                    val_str = str(val).strip()
                    if val_str.endswith('.0'):
                        val_str = val_str[:-2]
                    row_data[col] = val_str
                    has_data = True # 값이 하나라도 존재하면 유효 데이터

            if has_data:
                rows.append(row_data)

        # JSON 결과물 생성
        result_data = {
            "headers": headers,
            "raw_headers": raw_headers,
            "rows": rows
        }

        json_path = "data.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"🎉 [성공] 총 {len(rows)}건의 데이터를 '{json_path}' 파일로 저장했습니다!")
        print("=" * 50)

    except Exception as e:
        print(f"❌ [오류 발생] {e}")
        print("=" * 50)

if __name__ == "__main__":
    process_atis_excel()