import os
import json

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

    # AC 폴더 및 모든 하위 폴더(AC/Boeing 등)를 구석구석 탐색 (os.walk 사용)
    pdf_files = []
    for root, dirs, files in os.walk(ac_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                # 상대 경로 생성 (예: AC/Boeing/747-400.pdf)
                full_path = os.path.join(root, file).replace("\\", "/")
                pdf_files.append((file, full_path))

    for filename, rel_path in sorted(pdf_files):
        name_lower = filename.lower()
        path_lower = rel_path.lower()
        
        # 파일명이나 폴더 경로에 보잉/에어버스 키워드가 있는지 확인
        if any(keyword in name_lower or keyword in path_lower for keyword in ['707', '717', '727', '737', '747', '757', '767', '777', '787', 'boeing']):
            category = "Boeing"
            display_title = f"Boeing {filename.replace('.pdf', '')} Manual"
        elif any(keyword in name_lower or keyword in path_lower for keyword in ['a320', 'a330', 'a350', 'a380', 'airbus']):
            category = "Airbus"
            display_title = f"Airbus {filename.replace('.pdf', '')} Manual"
        else:
            category = "Others"
            display_title = f"{filename.replace('.pdf', '')} Manual"

        manuals_data[category].append({
            "title": display_title,
            "filename": filename,
            "path": rel_path
        })

    # manuals.json으로 저장
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(manuals_data, f, ensure_ascii=False, indent=2)

    print(f"🎉 성공: 총 {len(pdf_files)}개의 PDF 파일 목록을 '{json_output_path}'로 자동 생성했습니다!")

if __name__ == "__main__":
    generate_manuals_list()
