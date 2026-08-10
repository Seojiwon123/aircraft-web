import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def clean_boeing_filename(raw_filename):
    """
    보잉 파일명을 'B747-400.pdf' 스타일로 정제
    1. REV / Rev / rev 및 뒤에 오는 리비전 버전 문자열 완전 삭제
    2. 707, 737 등 숫자로 시작 시 앞에 'B' 추가
    """
    name, ext = os.path.splitext(raw_filename)
    if not ext or ext.lower() != '.pdf':
        ext = '.pdf'

    # 1. REV, Rev, rev 표시 및 뒤에 붙는 리비전 문자(예: _REV_E, _RevK, _Rev_F 등) 완전 제거
    cleaned = re.sub(r'[_.\s]?rev[_.\s]?[a-zA-Z0-9]+', '', name, flags=re.IGNORECASE)
    
    # 2. 혹시 남아있을 수 있는 단독 'rev' 단어 및 끝자리의 불필요한 언더바/하이픈 정돈
    cleaned = re.sub(r'[_.\s]?rev$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[-_]+$', '', cleaned)

    # 3. 707~787 등 7시리즈 숫자로 시작할 경우 맨 앞에 'B' 추가 (예: 737MAX -> B737MAX)
    if re.match(r'^7\d{2}', cleaned):
        cleaned = 'B' + cleaned

    return f"{cleaned}{ext}"


def download_boeing_7series_manuals():
    base_url = "https://www.boeing.com/commercial/airports/plan-manuals"
    save_dir = os.path.join("AC", "Boeing")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"📁 '{save_dir}' 폴더를 생성했습니다.")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("=" * 60)
    print(f"🌐 보잉 공식 웹페이지 접속 및 파일명 정제 수집 시작")
    print("=" * 60)

    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ 페이지 접속 실패 (HTTP 상태 코드: {response.status_code})")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        pdf_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().strip()

            if '.pdf' in href.lower():
                full_url = urljoin(base_url, href)
                
                # 7시리즈 항공기 필터링 (707~787)
                is_7series = re.search(r'7[0-9]{2}', href) or re.search(r'7[0-9]{2}', text)
                
                if is_7series:
                    raw_filename = href.split('/')[-1]
                    pdf_links.append((full_url, raw_filename))

        # 중복 링크 제거
        pdf_links = list(set(pdf_links))
        print(f"🎯 탐색 완료: 총 {len(pdf_links)}개의 보잉 매뉴얼 PDF를 찾았습니다.\n")

        downloaded_names = set()

        # 파일 다운로드 진행
        for idx, (pdf_url, raw_filename) in enumerate(pdf_links, 1):
            # 🔥 파일명 간결 정제 함수 적용 (예: 747-400_Rev_F.pdf -> B747-400.pdf)
            clean_filename = clean_boeing_filename(raw_filename)

            # 중복 이름 방지 (이름이 같을 경우 _2, _3 처리)
            final_name = clean_filename
            dup_count = 2
            while final_name in downloaded_names:
                base, ext = os.path.splitext(clean_filename)
                final_name = f"{base}_{dup_count}{ext}"
                dup_count += 1

            downloaded_names.add(final_name)
            save_path = os.path.join(save_dir, final_name)

            print(f"[{idx}/{len(pdf_links)}] 📥 다운로드 및 정제 완료: {final_name}")

            try:
                pdf_res = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
                if pdf_res.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in pdf_res.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print(f"    ✅ 저장 성공: {save_path}")
                else:
                    print(f"    ❌ 실패 (HTTP {pdf_res.status_code}): {pdf_url}")

            except Exception as e:
                print(f"    ❌ 오류 발생: {e}")

        print("\n" + "=" * 60)
        print("🎉 모든 보잉 매뉴얼 다운로드 및 정제 작업이 완료되었습니다!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 전체 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    download_boeing_7series_manuals()
