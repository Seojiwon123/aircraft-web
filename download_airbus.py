import os
import time
from playwright.sync_api import sync_playwright

AIRBUS_URL = "https://www.aircraft.airbus.com/en/customer-care/fleet-wide-care/airport-operations-and-aircraft-characteristics/aircraft-characteristics"
MAX_FILE_SIZE = 90 * 1024 * 1024  # 90MB 제한 (깃허브 100MB 초과 방지)

def download_airbus_manuals():
    print("=" * 60)
    print("🌐 에어버스 매뉴얼 접속 및 가독성 높은 파일명으로 자동 수집 시작")
    print("=" * 60)

    save_dir = os.path.join("AC", "Airbus")
    os.makedirs(save_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto(AIRBUS_URL, timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)

            # 1. 쿠키 팝업 닫기
            try:
                cookie_btn = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept')").first
                if cookie_btn.is_visible(timeout=3000):
                    cookie_btn.click()
            except Exception:
                pass

            # 2. 접힌 카테고리 메뉴 전체 클릭하여 펼치기
            print("🔍 카테고리 메뉴(A320, A330 등) 자동 펼치는 중...")
            expand_buttons = page.locator("button[aria-expanded='false'], .accordion__header, .tab-title").all()
            for btn in expand_buttons:
                try:
                    if btn.is_visible():
                        btn.click()
                        time.sleep(0.3)
                except Exception:
                    continue

            time.sleep(2)

            # 3. PDF 다운로드 요소 탐색
            pdf_elements = page.locator("a[href*='.pdf']").all()
            print(f"🎯 총 {len(pdf_elements)}개의 PDF 매뉴얼 링크 발견!\n")

            downloaded_files = set()

            for idx, elem in enumerate(pdf_elements, 1):
                try:
                    if not elem.is_visible():
                        continue

                    # Playwright를 통해 사람이 직접 누르듯 클릭하여 다운로드 이벤트 수신
                    with page.expect_download(timeout=15000) as download_info:
                        elem.click(force=True)

                    download = download_info.value
                    
                    # 🔥 핵심: 브라우저가 인식한 실제 가독성 높은 파일명 추출
                    suggested_filename = download.suggested_filename

                    # 중복 다운로드 방지
                    if suggested_filename in downloaded_files:
                        continue
                    downloaded_files.add(suggested_filename)

                    save_path = os.path.join(save_dir, suggested_filename)
                    print(f"[{idx}] 📥 다운로드 중: {suggested_filename}")

                    # 임시 다운로드 수행 후 용량 체킹
                    temp_path = download.path()
                    if temp_path and os.path.exists(temp_path):
                        file_size = os.path.getsize(temp_path)
                        
                        if file_size > MAX_FILE_SIZE:
                            print(f"    ⚠️ 90MB 용량 초과로 제외됨: {suggested_filename}")
                            continue

                        # 정상 용량일 경우 가독성 높은 이름으로 최종 저장
                        download.save_as(save_path)
                        print(f"    ✅ 저장 완료: {suggested_filename}")

                except Exception as e:
                    # 클릭 불가 링크나 중복 링크 처리 스킵
                    continue

            print("\n" + "=" * 60)
            print("🎉 가독성 높은 파일명으로 에어버스 매뉴얼 수집이 완료되었습니다!")
            print("=" * 60)

        except Exception as e:
            print(f"❌ 작업 중 오류 발생: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    download_airbus_manuals()
