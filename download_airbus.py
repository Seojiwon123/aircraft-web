import os
import re
import time
import requests
from urllib.parse import urljoin, unquote
from playwright.sync_api import sync_playwright

AIRBUS_URL = "https://www.aircraft.airbus.com/en/customer-care/fleet-wide-care/airport-operations-and-aircraft-characteristics/aircraft-characteristics"
MAX_FILE_SIZE = 90 * 1024 * 1024  # 90MB 제한 (깃허브 용량 초과 방지)

def clean_airbus_filename(raw_filename, fallback_url=""):
    """
    복잡한 원본 파일명을 'A340(-500, 600).pdf' 스타일로 간결하게 정제
    """
    name = raw_filename.strip()
    
    # 확장자 분리
    base_name, ext = os.path.splitext(name)
    if not ext or ext.lower() != '.pdf':
        ext = '.pdf'

    # 1. 특수한 aca32101-jul-2026 형태 처리 (A321 계열)
    aca_match = re.search(r'aca(\d{3})\d*', base_name, re.IGNORECASE)
    if aca_match:
        model_num = aca_match.group(1) # 예: 321
        return f"A{model_num}{ext}"

    # 2. 대표 에어버스 기종 찾기 (A220, A300, A310, A320, A330, A340, A350, A380)
    model_match = re.search(r'(A\d{3})', base_name, re.IGNORECASE)
    if not model_match and fallback_url:
        model_match = re.search(r'(A\d{3})', fallback_url, re.IGNORECASE)

    if not model_match:
        # 기종 구분이 안 되는 일반 파일은 불필요 수식어만 정리
        clean_name = re.sub(r'^(Airbus-Commercial-Aircraft-AC-|AC_)', '', base_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'_\d{8}$', '', clean_name) # 날짜 제거
        return f"{clean_name}{ext}"

    model_name = model_match.group(1).upper() # 예: A340, A330

    # 3. 세부 시리즈(예: -500-600, -200-300, -700L, F400 등) 추출
    # 기종명 뒷부분 텍스트 가져오기
    after_model = base_name[model_match.end():]

    # 날짜 패턴(_20251201 등) 및 불필요 접미사 제거
    after_model = re.sub(r'_\d{8}.*', '', after_model)
    after_model = re.sub(r'-[a-zA-Z]{3}-\d{4}.*', '', after_model) # -Dec-2009 등 제거

    # 세부 시리즈 패턴 매칭 (예: -500-600 -> (-500, 600), -700L -> (-700L))
    series_parts = re.findall(r'([A-Za-z0-9]+)', after_model)
    
    # 3자 이상의 무작위 난수(해시값)나 일자 텍스트 제거
    series_parts = [p for p in series_parts if not (len(p) > 5 and not p.isdigit())]

    if series_parts:
        # 하이픈(-)으로 시작하는 숫자/시리즈 형식을 (-500, 600) 형태로 재조합
        formatted_series = ", ".join([f"-{p}" if not p.startswith('-') else p for p in series_parts])
        return f"{model_name}({formatted_series}){ext}"
    else:
        return f"{model_name}{ext}"


def download_airbus_manuals():
    print("=" * 60)
    print("🌐 에어버스 매뉴얼 접속 및 간결한 파일명 정제 수집 시작")
    print("=" * 60)

    save_dir = os.path.join("AC", "Airbus")
    os.makedirs(save_dir, exist_ok=True)

    pdf_links = []

    # 1. Playwright로 DOM 펼치고 PDF 링크 수집
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(AIRBUS_URL, timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)

            # 쿠키 팝업 닫기
            try:
                cookie_btn = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept')").first
                if cookie_btn.is_visible(timeout=3000):
                    cookie_btn.click()
            except Exception:
                pass

            # 카테고리 전체 펼치기
            print("🔍 카테고리 메뉴 자동 펼치는 중...")
            expand_buttons = page.locator("button[aria-expanded='false'], .accordion__header, .tab-title").all()
            for btn in expand_buttons:
                try:
                    if btn.is_visible():
                        btn.click()
                        time.sleep(0.2)
                except Exception:
                    continue

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            links = page.locator("a[href*='.pdf']").all()
            for a in links:
                try:
                    href = a.get_attribute("href")
                    if href:
                        full_url = urljoin(AIRBUS_URL, href)
                        pdf_links.append(full_url)
                except Exception:
                    continue

            pdf_links = list(set(pdf_links))
            print(f"🎯 총 {len(pdf_links)}개의 PDF 매뉴얼 링크 수집 완료!\n")

        except Exception as e:
            print(f"❌ 페이지 접속 및 링크 수집 중 오류: {e}")
            return
        finally:
            browser.close()

    # 2. requests 다운로드 및 파일명 간결 정제
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    downloaded_names = set()

    for idx, pdf_url in enumerate(pdf_links, 1):
        try:
            with requests.get(pdf_url, headers=headers, stream=True, timeout=30) as res:
                if res.status_code != 200:
                    continue

                # 용량 체킹 (90MB 제한)
                content_length = res.headers.get('Content-Length')
                if content_length and int(content_length) > MAX_FILE_SIZE:
                    size_mb = round(int(content_length) / (1024 * 1024), 2)
                    print(f"[{idx}] ⚠️ 용량 초과 스킵 ({size_mb} MB > 90 MB): {pdf_url.split('/')[-1]}")
                    continue

                # 서버 파일명 수신
                cd = res.headers.get('content-disposition')
                raw_filename = None
                if cd:
                    filenames = re.findall(r'filename\*=UTF-8\'\'([^;]+)', cd, re.IGNORECASE)
                    if not filenames:
                        filenames = re.findall(r'filename="?([^";]+)"?', cd, re.IGNORECASE)
                    if filenames:
                        raw_filename = unquote(filenames[0].strip())

                if not raw_filename:
                    raw_filename = pdf_url.split("/")[-1].split("?")[0]

                # 🔥 핵심: 정제 규칙 적용 (예: AC_A340-500-600.pdf -> A340(-500, 600).pdf)
                clean_filename = clean_airbus_filename(raw_filename, pdf_url)

                # 중복 다운로드 방지 (이름이 같을 경우 _2, _3 붙이기)
                final_name = clean_filename
                dup_count = 2
                while final_name in downloaded_names:
                    base, ext = os.path.splitext(clean_filename)
                    final_name = f"{base}_{dup_count}{ext}"
                    dup_count += 1

                downloaded_names.add(final_name)
                save_path = os.path.join(save_dir, final_name)

                print(f"[{idx}/{len(pdf_links)}] 📥 다운로드 및 정제 완료: {final_name}")

                with open(save_path, "wb") as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

        except Exception as e:
            print(f"[{idx}] ❌ 파일 다운로드 중 오류: {e}")

    print("\n" + "=" * 60)
    print("🎉 간결한 파일명으로 에어버스 매뉴얼 수집 완료!")
    print("=" * 60)

if __name__ == "__main__":
    download_airbus_manuals()
