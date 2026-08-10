import os
import time
import json
import pandas as pd
from playwright.sync_api import sync_playwright

# ATIS 항공기 등록현황 페이지 주소
ATIS_URL = "http://atis.koca.go.kr/ATIS/aircraft/forwardPage.do?pageUrl=aircraftRegStat01"

def download_atis_excel():
    """1단계: Playwright를 사용해 ATIS에서 엑셀 다운로드"""
    print("=" * 60)
    print("🚀 [1/2] ATIS 웹사이트 접속 및 엑셀 다운로드 시작")
    print("=" * 60)

    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    save_path = os.path.join(download_dir, "atis_aircraft_status.xlsx")

    with sync_playwright() as p:
        # CI/GitHub Actions 서버 환경을 위해 headless 모드로 설정
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            print("🌐 ATIS 페이지 접속 중...")
            page.goto(ATIS_URL, timeout=30000)
            print(f"✅ 접속 완료: {page.title()}")

            print("🔍 '엑셀 다운로드' 버튼 탐색 및 클릭...")
            excel_button = page.locator("text=엑셀").first

            if not excel_button.is_visible():
                excel_button = page.locator("a:has-text('엑셀'), button:has-text('엑셀'), img[alt*='엑셀']").first

            with page.expect_download(timeout=20000) as download_info:
                excel_button.click()

            download = download_info.value
            download.save_as(save_path)
            print(f"🎉 엑셀 다운로드 성공! 저장 위치: {save_path}\n")
            return save_path

        except Exception as e:
            print(f"❌ 엑셀 다운로드 실패: {e}\n")
            return None
        finally:
            browser.close()

def process_atis_excel(excel_path):
    """2단계: 다운로드받은 엑셀을 data.json으로 변환"""
    print("=" * 60)
    print("⚙️ [2/2] 엑셀 데이터 파싱 및 data.json 변환 시작")
    print("=" * 60)

    if not excel_path or not os.path.exists(excel_path):
        print("❌ 변환할 엑셀 파일이 존재하지 않습니다.")
        return

    try:
        # ATIS 엑셀 원본은 2번째 줄(header=1)이 데이터 제목
        df = pd.read_excel(excel_path, header=1)
        
        # 유효 컬럼 추출
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
                    has_data = True

            if has_data:
                rows.append(row_data)

        result_data = {
            "headers": headers,
            "raw_headers": raw_headers,
            "rows": rows
        }

        json_path = "data.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"🎉 성공: 총 {len(rows)}건의 항공기 등록 데이터를 '{json_path}'로 가공했습니다!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 엑셀 파싱 및 JSON 변환 오류: {e}")
        print("=" * 60)

if __name__ == "__main__":
    excel_file = download_atis_excel()
    if excel_file:
        process_atis_excel(excel_file)