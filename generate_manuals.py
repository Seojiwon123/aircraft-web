import os
import json

def generate_manuals_list():
    ac_dir = "AC"
    json_output_path = "manuals.json"

    # 기본 생성 데이터 구조 (추후 에어버스 등 추가 가능)
    manuals_data = {
        "Boeing": [],
        "Airbus": [],
        "Others": []
    }

    if not os.path.exists(ac_dir):
        os.makedirs(ac_dir)
        print(f"📁 '{ac_dir}' 폴더가 생성되었습니다. PDF 파일들을 넣고 다시 실행해 주세요.")

    # AC 폴더 내의 모든 PDF 파일 탐색
    files = [f for f in os.listdir(ac_dir) if f.lower().endswith('.pdf')]

    for filename in sorted(files):
        # 파일명을 보기 좋은 제목 형태로 변환 (예: 747-400_Rev_F.pdf -> Boeing 747-400 Manual)
        name_lower = filename.lower()
        
        # 기본 제조사 분류 규칙
        if any(keyword in name_lower for keyword in ['737', '747', '767', '777', '787', 'boeing']):
            category = "Boeing"
            display_title = f"Boeing {filename.replace('.pdf', '')} Manual"
        elif any(keyword in name_lower for keyword in ['a320', 'a330', 'a350', 'a380', 'airbus']):
            category = "Airbus"
            display_title = f"Airbus {filename.replace('.pdf', '')} Manual"
        else:
            category = "Others"
            display_title = f"{filename.replace('.pdf', '')} Manual"

        manuals_data[category].append({
            "title": display_title,
            "filename": filename,
            "path": f"AC/{filename}"
        })

    # manuals.json으로 저장
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(manuals_data, f, ensure_ascii=False, indent=2)

    print(f"🎉 성공: 총 {len(files)}개의 PDF 파일 목록을 '{json_output_path}'로 자동 생성했습니다!")

if __name__ == "__main__":
    generate_manuals_list()