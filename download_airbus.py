import os
import time
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# 에어버스 항공기 제원 매뉴얼 공식 페이지
AIRBUS_URL = "https://www.aircraft.airbus.com/en/customer-care/fleet-wide-care/airport-operations-and-aircraft-characteristics/aircraft-characteristics"

def download_airbus_manuals():
    print("=" * 60)
    print("🌐 에어버스 공식 웹페이지 접속 및 동적 매뉴얼 탐색 시작")
    print("=" * 60)

    save_dir = os.path.join("AC", "Airbus")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"📁 '{save_dir}' 폴더를 생성했습니다.")

    with sync_playwright() as p:
        # headless 브라우저 구동
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(AIRBUS_URL, timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)
            print(f"✅ 페이지 접속 성공: {page.title()}")

            # 1. 쿠키 승인 팝업이 있을 경우 클릭하여 닫기
            try:
                cookie_btn = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept'), button:has-text('Agree')").first
                if cookie_btn.is_visible(timeout=3000):
                    cookie_btn.click()
                    time.sleep(1)
            except Exception:
                pass

            # 2. 접혀 있는 기종별 아코디언/탭 버튼 전체 탐색 및 자동 클릭
            print("🔍 카테고리 메뉴(A320, A330, A350 등) 자동 열기 진행 중...")
            expand_buttons = page.locator("button[aria-expanded='false'], .accordion__header, .tab-title").all()
            for btn in expand_buttons:
                try:
                    if btn.is_visible():
                        btn.click()
                        time.sleep(0.5)
                except Exception:
                    continue

            # 페이지 바닥까지 스크롤하여 모든 동적 데이터 로딩
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # 3. 화면에 노출된 모든 PDF 다운로드 링크 수집
            pdf_links = []
            links = page.locator("a[href*='.pdf']").all()
            
            for a in links:
                try:
                    href = a.get_attribute("href")
                    if href:
                        full_url = urljoin(AIRBUS_URL, href)
                        # 파일명 추출 (URL 파라미터 제거)
                        filename = full_url.split("/")[-1].split("?")[0]
                        if filename.lower().endswith('.pdf'):
                            pdf_links.append((full_url, filename))
                except Exception:
                    continue

            # 중복 링크 제거
            pdf_links = list(set(pdf_links))
            print(f"🎯 탐색 완료: 총 {len(pdf_links)}개의 에어버스 매뉴얼 PDF를 찾았습니다.\n")

            # 4. 파일 다운로드 실행
            headers = {"User-Agent": "Mozilla/5.0"}
            for idx, (pdf_url, filename) in enumerate(pdf_links, 1):
                save_path = os.path.join(save_dir, filename)
                print(f"[{idx}/{len(pdf_links)}] 📥 다운로드 중: {filename}")

                try:
                    res = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
                    if res.status_code == 200:
                        with open(save_path, "wb") as f:
                            for chunk in res.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        print(f"    ✅ 저장 완료: {save_path}")
                    else:
                        print(f"    ❌ 실패 (HTTP {res.status_code}): {pdf_url}")
                except Exception as e:
                    print(f"    ❌ 다운로드 오류: {e}")

            print("\n" + "=" * 60)
            print("🎉 모든 에어버스 매뉴얼 수집 및 다운로드가 완료되었습니다!")
            print("=" * 60)

        except Exception as e:
            print(f"❌ 처리 중 에러 발생: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    download_airbus_manuals()