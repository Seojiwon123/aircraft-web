import os
import json

# 💡 GitHub 계정 및 저장소 정보
GITHUB_USER = "Seojiwon123"      # 본인 GitHub ID
REPO_NAME = "aircraft-web"     # 실제 저장소 이름으로 변경 (예: aircraft-status)
BRANCH_NAME = "main"             # 기본 브랜치명

def generate_manuals_list():
    ac_dir = "AC"
    json_output_path = "manuals.json"

    manuals_data = {
        "Boeing": [],
        "Airbus": [],
        "Others": []
    }

    if not os.path.exists(ac_dir):
        os.makedirs(ac_dir)
        print(f"📁 '{ac_dir}' 폴더가 생성되었습니다.")

    # AC 폴더 및 하위 폴더 전체 탐색
    pdf_files = []
    for root, dirs, files in os.walk(ac_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                # 윈도우/맥 경로 구분자 표준화 (/)
                full_path = os.path.join(root, file).replace("\\", "/")
                pdf_files.append((file, full_path, root.replace("\\", "/")))

    for filename, rel_path, folder_path in sorted(pdf_files):
        folder_lower = folder_path.lower()
        name_lower = filename.lower()
        
        # 1. 'AC/Boeing' 폴더 안에 있거나 파일명/경로에 보잉 키워드가 있으면 무조건 Boeing 탭으로 지정
        if "boeing" in folder_lower or "boeing" in name_lower or any(k in name_lower for k in ['707', '717', '720', '727', '737', '747', '757', '767', '777', '787']):
            category = "Boeing"
        # 2. 'AC/Airbus' 폴더 안에 있거나 에어버스 키워드가 있으면 Airbus 탭으로 지정
        elif "airbus" in folder_lower or "airbus" in name_lower or any(k in name_lower for k in ['a300', 'a310', 'a320', 'a330', 'a340', 'a350', 'a380']):
            category = "Airbus"
        else:
            category = "Others"

        # 화면에는 확장자(.pdf)만 뗀 실제 파일명 그대로 표시
        display_title = os.path.splitext(filename)[0]

        # 💡 핵심: GitHub Pages 텍스트 포인터 대신 LFS 원본 직접 다운로드 URL 생성
        raw_download_url = f"https://media.githubusercontent.com/media/{GITHUB_USER}/{REPO_NAME}/{BRANCH_NAME}/{rel_path}"

        manuals_data[category].append({
            "title": display_title,
            "filename": filename,
            "path": raw_download_url
        })

    # manuals.json으로 저장
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(manuals_data, f, ensure_ascii=False, indent=2)

    print(f"🎉 성공: 총 {len(pdf_files)}개의 PDF 파일 목록을 LFS 원본 링크 형태의 '{json_output_path}'로 자동 생성했습니다!")

if __name__ == "__main__":
    generate_manuals_list()
