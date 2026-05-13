import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

CATEGORY_RULES = {
    "01_identity": [
        "신분증", "주민등록증", "운전면허", "여권", "인감증명", "본인서명", "위임장"
    ],
    "02_transfer_sale": [
        "양도계약", "매도계약", "매매계약", "양도", "매도", "중개수수료", "입금내역"
    ],
    "03_acquisition": [
        "취득계약", "매수계약", "경매", "낙찰", "취득세", "등록세", "법무사", "배당표"
    ],
    "04_expenses": [
        "필요경비", "인테리어", "에어컨", "시스템에어컨", "옵션", "공사", "세금계산서", "영수증", "이체"
    ],
    "05_registry": [
        "등기부", "등기사항", "건축물대장", "토지대장", "공시지가"
    ],
    "06_residence": [
        "주민등록초본", "주민등록등본", "초본", "등본", "전입", "거주", "공과금"
    ],
    "07_rental_house": [
        "임대사업자", "민간임대", "렌트홈", "임대차", "임대계약", "임대료", "5%", "등록말소"
    ],
    "08_redevelopment": [
        "재건축", "재개발", "관리처분", "사업시행", "권리가액", "분담금", "청산금", "조합", "준공", "이전고시"
    ],
    "09_tax_filing_delegation": [
        "수임동의", "세무대리", "신고대행", "최종확인", "수수료", "업무범위", "성실확인"
    ],
}

ALLOWED_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".hwp", ".hwpx",
    ".docx", ".xlsx", ".xls", ".txt", ".csv"
}

def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "attachment_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")

def get_category(filename):
    name_lower = filename.lower()
    for cat, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in name_lower:
                return cat, f"filename_keyword: {kw}"
    return "99_others", "no_keyword_match"

def write_manifest(attach_dir, case_id, source_dir, file_records):
    manifest = {
        "case_id": case_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_dir": str(source_dir),
        "files": file_records,
        "summary": {
            "total_files": len(file_records),
            "by_category": {}
        }
    }
    
    for rec in file_records:
        cat = rec["category"]
        manifest["summary"]["by_category"][cat] = manifest["summary"]["by_category"].get(cat, 0) + 1
        
    manifest_path = attach_dir / "attachment_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    return manifest_path, manifest

def write_checklist(attach_dir, case_id, source_dir, manifest):
    lines = []
    lines.append("# 세무사 송부용 첨부서류 체크리스트")
    lines.append("")
    lines.append(f"사건번호: {case_id}")
    lines.append(f"생성일: {manifest['created_at']}")
    lines.append(f"원본 폴더: {source_dir}")
    lines.append("")
    lines.append("## 첨부 요약")
    lines.append("")
    lines.append(f"- 총 첨부파일 수: {manifest['summary']['total_files']}")
    
    cat_counts = manifest["summary"]["by_category"]
    
    labels = {
        "01_identity": "본인확인/위임",
        "02_transfer_sale": "양도 관련",
        "03_acquisition": "취득 관련",
        "04_expenses": "필요경비",
        "05_registry": "등기/물건",
        "06_residence": "거주",
        "07_rental_house": "장기임대주택",
        "08_redevelopment": "재개발·재건축",
        "09_tax_filing_delegation": "신고대행 위임",
        "99_others": "기타"
    }
    
    for cat, label in labels.items():
        count = cat_counts.get(cat, 0)
        lines.append(f"- {label}: {count}")
        
    lines.append("")
    lines.append("## 세무사 확인 필요")
    lines.append("")
    lines.append("- 미분류 파일은 99_others에서 확인")
    lines.append("- 파일명만으로 자동분류한 것이므로 최종 서류 성격은 세무사 또는 담당자가 확인 필요")
    lines.append("")
    
    checklist_path = attach_dir / "attachment_checklist.md"
    with open(checklist_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    return checklist_path

def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 세무사 송부용 첨부서류 분류")
    parser.add_argument("case_id", help="사건번호")
    parser.add_argument("--source", required=True, help="원본 파일 폴더 경로")
    parser.add_argument("--copy", action="store_true", help="원본 파일 복사 (기본)")
    parser.add_argument("--move", action="store_true", help="원본 파일 이동")
    parser.add_argument("--dry-run", action="store_true", help="실제 복사 없이 분류 결과만 출력")
    parser.add_argument("--overwrite", action="store_true", help="동일 파일 존재 시 덮어쓰기")
    parser.add_argument("--prefix-date", action="store_true", help="파일명 앞에 처리일자 붙이기")
    
    args = parser.parse_args()
    case_id = args.case_id
    source_dir = Path(args.source)
    is_move = args.move
    is_dry_run = args.dry_run
    
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"[FAIL] 원본 폴더를 찾을 수 없습니다: {source_dir}")
        return
        
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        if is_dry_run:
            print(f"[WARN] 사건 폴더가 존재하지 않지만 dry-run 이므로 계속 진행: {case_dir}")
        else:
            print(f"[FAIL] 사건 폴더를 찾을 수 없습니다: {case_dir}")
            return
            
    attach_dir = case_dir / "11_attachments"
    if not is_dry_run:
        attach_dir.mkdir(exist_ok=True)
        for cat in CATEGORY_RULES.keys():
            (attach_dir / cat).mkdir(exist_ok=True)
        (attach_dir / "99_others").mkdir(exist_ok=True)
        
    file_records = []
    
    for fpath in source_dir.iterdir():
        if not fpath.is_file():
            continue
            
        ext = fpath.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
            
        cat, reason = get_category(fpath.name)
        
        target_name = fpath.name
        if args.prefix_date:
            today_str = datetime.now().strftime("%Y%m%d")
            target_name = f"{today_str}_{target_name}"
            
        target_path = attach_dir / cat / target_name
        
        file_records.append({
            "original_name": fpath.name,
            "stored_name": target_name,
            "category": cat,
            "stored_path": str(target_path) if not is_dry_run else f"DRY_RUN: {target_path}",
            "extension": ext,
            "size_bytes": fpath.stat().st_size,
            "classification_reason": reason
        })
        
        if not is_dry_run:
            if target_path.exists() and not args.overwrite:
                pass
            else:
                if is_move:
                    shutil.move(fpath, target_path)
                else:
                    shutil.copy2(fpath, target_path)
                    
    if is_dry_run:
        print("[DRY-RUN] 첨부서류 분류 결과")
        for rec in file_records:
            print(f"[{rec['category']}] {rec['original_name']} -> {rec['classification_reason']}")
        return
        
    manifest_path, manifest = write_manifest(attach_dir, case_id, source_dir, file_records)
    checklist_path = write_checklist(attach_dir, case_id, source_dir, manifest)
    
    write_log(case_id, f"attachments_processed files={len(file_records)}")
    
    print("[SUCCESS] 첨부서류 분류 완료")
    print(f"[CASE_ID] {case_id}")
    print(f"[ATTACH_DIR] {attach_dir}")
    print(f"[MANIFEST] {manifest_path}")
    print(f"[CHECKLIST] {checklist_path}")
    print(f"[TOTAL_FILES] {len(file_records)}")

if __name__ == "__main__":
    main()
