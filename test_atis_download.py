import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright

# 1. ATIS 항공기 등록현황 페이지 주소
ATIS_URL = "http://atis.koca.go.kr/ATIS/aircraft/forwardPage.do?pageUrl=aircraftRegStat01"

def test_atis_excel_download():
    print("🚀 [1/4] 브라우저를 시작하고 ATIS 페이지로 이동합니다...")

    with sync_playwright() as p:
        # headless=False 로 지정하면 브라우저가 직접 열려 동작 과정을 눈으로 확인할 수 있습니다.
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            # ATIS 웹사이트 접속
            page.goto(ATIS_URL, timeout=30000)
            print(f"✅ 페이지 접속 완료: {page.title()}")

            print("🔍 [2/4] '엑셀 다운로드' 버튼 찾는 중...")
            
            # 페이지 내에서 '엑셀', 'Excel', 또는 해당 다운로드 버튼/이미지 검색
            # ATIS 웹사이트 상의 버튼 텍스트나 selector를 지정합니다.
            excel_button = page.locator("text=엑셀").first

            if not excel_button.is_visible():
                print("⚠️ '엑셀' 텍스트 버튼을 찾지 못해 이미지/버튼 셀렉터 탐색을 시도합니다.")
                excel_button = page.locator("a:has-text('엑셀'), button:has-text('엑셀'), img[alt*='엑셀']").first

            print("🖱️ [3/4] 엑셀 다운로드 버튼 클릭 및 파일 수신 대기...")

            # 다운로드 이벤트가 발생하는 순간을 캡처
            with page.expect_download(timeout=15000) as download_info:
                excel_button.click()

            download = download_info.value

            # 저장할 파일 경로 설정
            download_dir = os.path.join(os.getcwd(), "downloads")
            os.makedirs(download_dir, exist_ok=True)
            save_path = os.path.join(download_dir, "atis_aircraft_status.xlsx")

            # 파일 저장
            download.save_as(save_path)
            print(f"🎉 [4/4] 엑셀 다운로드 성공! 저장 위치: {save_path}")

            # 다운로드받은 엑셀 파일 정상 동작 및 내용 확인
            time.sleep(1)
            if os.path.exists(save_path):
                print("\n📊 --- 다운로드된 엑셀 파일 상위 데이터 확인 ---")
                # ATIS 엑셀 특성상 상단에 제목 행이 있을 수 있어 header 위치 조정 가능
                df = pd.read_excel(save_path)
                print(df.head(5))

        except Exception as e:
            print(f"\n❌ 다운로드 테스트 중 오류가 발생했습니다: {e}")
            print("💡 팁: ATIS 웹사이트의 '엑셀 다운로드' 버튼 ID나 Selector를 구체적으로 지정해주어야 할 수 있습니다.")

        finally:
            browser.close()

if __name__ == "__main__":
    test_atis_excel_download()