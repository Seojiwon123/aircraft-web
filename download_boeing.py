import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def download_boeing_7series_manuals():
    # 1. 보잉 매뉴얼 공식 페이지 URL
    base_url = "https://www.boeing.com/commercial/airports/plan-manuals"
    # 기존 코드에서 save_dir 부분을 아래와 같이 변경합니다.
    save_dir = os.path.join("AC", "Boeing")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"📁 '{save_dir}' 폴더를 생성했습니다.")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("=" * 60)
    print(f"🌐 보잉 공식 웹페이지 접속 중: {base_url}")
    print("=" * 60)

    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ 페이지 접속 실패 (HTTP 상태 코드: {response.status_code})")
            return

        # 2. HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. 모든 a 태그(링크) 수집 및 PDF 파일 탐색
        pdf_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().strip()

            # URL 또는 링크 텍스트에 '.pdf'가 포함된 경우
            if '.pdf' in href.lower():
                full_url = urljoin(base_url, href)
                
                # 7시리즈 항공기 필터링 (707, 717, 727, 737, 747, 757, 767, 777, 787 등)
                # 파일명이나 링크 텍스트에 707~787 패턴이 포함되어 있는지 확인
                is_7series = re.search(r'7[0-9]{2}', href) or re.search(r'7[0-9]{2}', text)
                
                if is_7series:
                    pdf_links.append((full_url, href.split('/')[-1]))

        # 중복 링크 제거
        pdf_links = list(set(pdf_links))

        print(f"🎯 탐색 완료: 총 {len(pdf_links)}개의 7시리즈 매뉴얼 PDF를 찾았습니다.\n")

        # 4. 파일 다운로드 진행
        for idx, (pdf_url, file_name) in enumerate(pdf_links, 1):
            save_path = os.path.join(save_dir, file_name)
            print(f"[{idx}/{len(pdf_links)}] 📥 다운로드 중: {file_name}")

            try:
                pdf_res = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
                if pdf_res.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in pdf_res.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print(f"    ✅ 성공: {save_path}")
                else:
                    print(f"    ❌ 실패 (HTTP {pdf_res.status_code}): {pdf_url}")

            except Exception as e:
                print(f"    ❌ 오류 발생: {e}")

        print("\n" + "=" * 60)
        print("🎉 모든 7시리즈 매뉴얼 다운로드 작업이 완료되었습니다!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 전체 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    download_boeing_7series_manuals()