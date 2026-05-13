import argparse
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"


def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "export_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")


def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir


def read_json_if_exists(path):
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def ensure_clean_export_dir(case_id):
    EXPORTS_DIR.mkdir(exist_ok=True)

    export_dir = EXPORTS_DIR / case_id

    if export_dir.exists():
        shutil.rmtree(export_dir)

    export_dir.mkdir(parents=True, exist_ok=True)

    subdirs = [
        "00_manifest",
        "01_reports",
        "01_reports_docx",
        "02_extract",
        "02_consents",
        "03_missing",
        "04_transcript",
        "05_documents",
        "06_audio",
        "07_attachments",
    ]

    for subdir in subdirs:
        (export_dir / subdir).mkdir(exist_ok=True)

    return export_dir


def copy_file_if_exists(src, dst_dir, copied_files, label):
    if not src.exists() or not src.is_file():
        return None

    dst_dir.mkdir(exist_ok=True)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)

    copied_files.append({
        "label": label,
        "source": str(src),
        "exported": str(dst),
        "filename": dst.name,
        "size_bytes": dst.stat().st_size,
    })

    return dst


def copy_dir_files(src_dir, dst_dir, copied_files, label):
    if not src_dir.exists():
        return []

    dst_dir.mkdir(exist_ok=True)
    copied = []

    for src in src_dir.iterdir():
        if not src.is_file():
            continue

        dst = dst_dir / src.name
        shutil.copy2(src, dst)

        item = {
            "label": label,
            "source": str(src),
            "exported": str(dst),
            "filename": dst.name,
            "size_bytes": dst.stat().st_size,
        }
        copied_files.append(item)
        copied.append(dst)

    return copied


def write_manifest(export_dir, case_id, case_dir, copied_files, include_audio):
    meta = read_json_if_exists(case_dir / "case_meta.json")
    tax_data = read_json_if_exists(case_dir / "04_extract" / "tax_facts.json")
    acq_data = read_json_if_exists(case_dir / "04_extract" / "acquisition_price_review.json")

    manifest = {
        "case_id": case_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_case_dir": str(case_dir),
        "include_audio": include_audio,
        "case_status": meta.get("status", ""),
        "case_type": tax_data.get("case_type", meta.get("case_type", "")),
        "risk_level": tax_data.get("risk_level", meta.get("risk_level", "")),
        "real_estate_office": meta.get("real_estate_office", ""),
        "manager_name": meta.get("manager_name", ""),
        "client_name": meta.get("client_name", ""),
        "property_address": (
            tax_data.get("facts", {}).get("property_address")
            or meta.get("property_address", "")
        ),
        "missing_items": tax_data.get("missing_items", []),
        "acquisition_price_confidence_grade": acq_data.get("confidence_grade", ""),
        "acquisition_price_confidence_reason": acq_data.get("confidence_reason", ""),
        "acquisition_price_tax_accountant_required": acq_data.get("tax_accountant_required", ""),
        "acquisition_price_replacement_review_required": acq_data.get("needs_replacement_review", ""),
        "acquisition_price_missing_core_evidence": acq_data.get("missing_core_evidence", []),
        "copied_file_count": len(copied_files),
        "copied_files": copied_files,
        "notice": "본 패키지는 세무사 검토용 사건 정리 자료이며 세무 판단 확정 또는 신고서가 아닙니다.",
    }

    manifest_path = export_dir / "00_manifest" / "manifest.json"

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest_path, manifest


def write_readme(export_dir, case_id, manifest):
    missing_items = manifest.get("missing_items", [])

    lines = []
    lines.append(f"# {case_id} 세무사 검토용 사건 패키지")
    lines.append("")
    lines.append("## 1. 패키지 개요")
    lines.append("")
    lines.append(f"- 사건번호: {case_id}")
    lines.append(f"- 생성일시: {manifest.get('created_at', '')}")
    lines.append(f"- 사건유형: {manifest.get('case_type', '') or '미확정'}")
    lines.append(f"- 위험등급: {manifest.get('risk_level', '') or '미확정'}")
    lines.append(f"- 부동산 사무실: {manifest.get('real_estate_office', '') or '미입력'}")
    lines.append(f"- 담당자: {manifest.get('manager_name', '') or '미입력'}")
    lines.append(f"- 고객명: {manifest.get('client_name', '') or '미입력'}")
    lines.append(f"- 대상 부동산: {manifest.get('property_address', '') or '미확인'}")
    lines.append("")
    lines.append("## 2. 폴더 구성")
    lines.append("")
    lines.append("| 폴더 | 내용 |")
    lines.append("|---|---|")
    lines.append("| 01_reports | 고객용/부동산용/세무사용 리포트 |")
    lines.append("| 01_reports_docx | 세무사 검토 및 출력용 DOCX 리포트 |")
    lines.append("| 02_extract | 양도세 사실관계 추출 JSON |")
    lines.append("| 02_consents | 신고대행 위임 및 확인 서류 |")
    lines.append("| 03_missing | 누락자료 목록 및 고객 보완요청 문구 |")
    lines.append("| 04_transcript | 상담 녹취록 텍스트 |")
    lines.append("| 05_documents | 계약서, 등기부, 사진, PDF 등 증빙자료 |")
    lines.append("| 06_audio | 상담 녹음파일 |")
    lines.append("| 07_attachments | 세무사 송부용 추가 첨부 증빙서류 |")
    lines.append("")
    lines.append("## 리포트 파일 안내")
    lines.append("")
    lines.append("본 패키지에는 Markdown 리포트와 Word(DOCX) 리포트가 함께 포함되어 있습니다.")
    lines.append("")
    lines.append("- Markdown 리포트: 시스템 원본 리포트")
    lines.append("- DOCX 리포트: 세무사 검토 및 출력용 문서")
    lines.append("")
    lines.append("우선 확인 권장 파일:")
    lines.append("1. 03_tax_accountant_review.docx")
    lines.append("2. legal_basis_check.json")
    lines.append("3. regulated_area_check.json")
    lines.append("4. acquisition_price_review.json")
    lines.append("5. multi_asset_split_review.json")
    lines.append("6. redevelopment_legal_review.json")
    lines.append("7. case_risk_grade.json")
    lines.append("")
    
    risk_grade_path = export_dir / "02_extract" / "case_risk_grade.json"
    risk_grade_data = {}
    if risk_grade_path.exists():
        try:
            with open(risk_grade_path, "r", encoding="utf-8") as f:
                risk_grade_data = json.load(f)
        except Exception:
            pass

    if risk_grade_data:
        grade = risk_grade_data.get("grade", "미확인")
        color = risk_grade_data.get("color", "미확인")
        grade_name = risk_grade_data.get("grade_name", "미확인")
        req = "Y" if risk_grade_data.get("tax_accountant_required") else "N"
        review_fee = risk_grade_data.get("recommended_tax_review_fee", "미확인")
        filing_fee = risk_grade_data.get("tax_filing_fee", "미확인")
        reasons = risk_grade_data.get("reasons", [])
        reason_str = ", ".join(reasons) if reasons else "단순 사건"
        
        lines.append("## 사건등급 및 수수료 기준")
        lines.append("")
        lines.append("본 사건의 TaxCaseManager 등급:")
        lines.append(f"- 등급: {grade}")
        lines.append(f"- 색상: {color}")
        lines.append(f"- 등급명: {grade_name}")
        lines.append(f"- 세무사 검토 필요: {req}")
        lines.append(f"- 세무사 검토비 기준: {review_fee}")
        lines.append(f"- 실제 신고대행 수수료: {filing_fee}")
        lines.append(f"- 주요 사유: {reason_str}")
        lines.append("")
        lines.append("본 등급은 사전진단 및 업무량 판단을 위한 기준이며, 세무사 최종 수임 여부와 수수료는 별도 협의가 필요합니다.")
        lines.append("")
    
    lines.append("## 3. 세무사 우선 확인 항목")
    lines.append("")
    if missing_items:
        for item in missing_items:
            lines.append(f"- {item}")
    else:
        lines.append("- 현재 1차 기준 누락항목 없음")
    lines.append("")

    regulated_area_path = export_dir / "02_extract" / "regulated_area_check.json"
    regulated_area_data = {}
    if regulated_area_path.exists():
        try:
            with open(regulated_area_path, "r", encoding="utf-8") as f:
                regulated_area_data = json.load(f)
        except Exception:
            pass

    if regulated_area_data:
        lines.append("## 조정대상지역 이력 확인")
        lines.append("")
        lines.append(f"- 기준일: {regulated_area_data.get('basis_date', '')} ({regulated_area_data.get('basis_date_type', '')})")
        lines.append(f"- 지역: {regulated_area_data.get('region', '')}")
        lines.append(f"- 조정대상지역 여부: {regulated_area_data.get('is_adjustment_target_area', '')}")
        lines.append(f"- 신뢰도: {regulated_area_data.get('confidence', '')}")
        tax_rev_req = "Y" if regulated_area_data.get("tax_review_required") else "N"
        lines.append(f"- 세무사 검토 필요: {tax_rev_req}")
        lines.append("")
    
    grade = manifest.get("acquisition_price_confidence_grade", "미확인")
    tax_req = "Y" if manifest.get("acquisition_price_tax_accountant_required") else "N"
    rep_req = "conditional" if not manifest.get("acquisition_price_replacement_review_required") else "Y"
    acq_missing = manifest.get("acquisition_price_missing_core_evidence", [])
    
    lines.append("## 취득가액 검토 요약")
    lines.append("")
    lines.append(f"- 취득가액 신뢰도: {grade}")
    lines.append(f"- 세무사 필수 검토: {tax_req}")
    lines.append(f"- 대체 취득가액 검토 필요 여부: {rep_req}")
    lines.append("- 부족한 핵심 증빙:")
    if acq_missing:
        for item in acq_missing:
            lines.append(f"  - {item}")
    else:
        lines.append("  - 없음")
    lines.append("")
    lines.append("주의:")
    lines.append("취득가액은 양도세 계산에 직접 영향을 주는 핵심 항목입니다.")
    lines.append("본 패키지는 취득가액을 확정하지 않으며,")
    lines.append("최종 취득가액 산정은 세무사 검토가 필요합니다.")
    lines.append("")
    
    legal_basis_path = export_dir / "02_extract" / "legal_basis_check.json"
    legal_basis_data = {}
    if legal_basis_path.exists():
        try:
            with open(legal_basis_path, "r", encoding="utf-8") as f:
                legal_basis_data = json.load(f)
        except Exception:
            pass

    if legal_basis_data:
        lines.append("## 법령 기준 확인")
        lines.append("")
        lines.append(f"- 법령 DB 상태: {legal_basis_data.get('legal_basis_status', '미확인')}")
        lines.append(f"- 마지막 확인일: {legal_basis_data.get('legal_basis_last_checked', '미확인')}")
        reg_db = legal_basis_data.get("regulated_area_db", {})
        lines.append(f"- 조정대상지역 DB 감사 상태: OK {reg_db.get('ok_count', 0)}건, PARTIAL {reg_db.get('partial_only_count', 0)}건")
        
        laws = legal_basis_data.get("laws", [])
        detail_req = any(law.get("detail_article_check_required") for law in laws)
        lines.append(f"- 세부 조문 확인 필요: {'Y' if detail_req else 'N'}")
        tax_rev = "Y" if legal_basis_data.get("tax_accountant_review_required") else "N"
        lines.append(f"- 세무사 최종 검토 필요: {tax_rev}")
        lines.append("")
    
    lines.append("## 4. 권장 검토 순서")
    lines.append("")
    lines.append("1. `01_reports\\03_tax_accountant_review.md`를 먼저 확인한다.")
    lines.append("2. `02_extract\\tax_facts.json`에서 추출된 사실관계를 확인한다.")
    lines.append("3. `03_missing\\missing_items.md`에서 미확인 항목을 확인한다.")
    lines.append("4. `05_documents`의 증빙자료를 대조한다.")
    lines.append("5. 필요 시 `04_transcript\\transcript.txt`에서 상담 원문을 확인한다.")
    lines.append("6. 녹음파일 검토가 필요할 경우 `06_audio`를 확인한다.")
    lines.append("")
    lines.append("## 5. 주의")
    lines.append("")
    lines.append("본 패키지는 고객 진술 및 제출자료를 기반으로 한 사건 정리 자료입니다.")
    lines.append("본 패키지 자체는 세무 판단 확정 또는 양도소득세 신고서가 아닙니다.")
    lines.append("최종 판단 및 신고는 세무사의 검토와 책임 하에 진행되어야 합니다.")
    lines.append("부동산 사무실은 세무 판단을 확정하지 않습니다.")
    lines.append("")
    lines.append("## 신고대행 전환 시 필수 확인서류")
    lines.append("")
    lines.append("실제 양도소득세 신고대행으로 전환하는 경우, 사전진단 및 세무사 검토와 별도로 고객 위임 및 본인확인 절차가 필요할 수 있습니다.")
    lines.append("")
    lines.append("확인 대상:")
    lines.append("- 고객 제공자료 성실확인 및 불이익 고지서")
    lines.append("- 양도소득세 신고대행 위임 및 본인확인 안내서")
    lines.append("- 세무사 신고대행 수수료 및 업무범위 확인서")
    lines.append("- 최종 신고내용 확인서")
    lines.append("")
    lines.append("주의:")
    lines.append("인감증명서 또는 본인서명사실확인서, 신분증 사본, 홈택스 수임동의 등은 세무사 사무실 기준과 사건 난이도에 따라 추가로 요구될 수 있습니다.")
    lines.append("")
    lines.append("## 첨부 증빙서류 안내")
    lines.append("")
    lines.append("본 패키지에는 고객 또는 부동산 사무실에서 제출한 증빙서류가 포함될 수 있습니다.")
    lines.append("")
    lines.append("첨부서류 위치:")
    lines.append("- 07_attachments/")
    lines.append("")
    lines.append("주요 분류:")
    lines.append("- 본인확인/위임")
    lines.append("- 양도계약/매도자료")
    lines.append("- 취득계약/경매/취득세 자료")
    lines.append("- 필요경비/옵션/공사비 자료")
    lines.append("- 등기부/건축물대장")
    lines.append("- 주민등록/거주자료")
    lines.append("- 장기임대주택 관련 자료")
    lines.append("- 재개발·재건축 관련 자료")
    lines.append("")
    lines.append("주의:")
    lines.append("첨부파일은 파일명 기준으로 1차 자동분류된 것이므로, 세무사 검토 시 최종 서류 성격을 다시 확인해야 합니다.")
    lines.append("")

    readme_path = export_dir / "00_manifest" / "README_FOR_TAX_ACCOUNTANT.md"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return readme_path


def zip_export_dir(export_dir, case_id):
    zip_path = EXPORTS_DIR / f"{case_id}.zip"

    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in export_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(EXPORTS_DIR)
                zf.write(file_path, arcname)

    return zip_path


def update_case_meta(case_dir, zip_path):
    meta_path = case_dir / "case_meta.json"
    if not meta_path.exists():
        return

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        meta["status"] = "06_EXPORTED"
        meta["exported_at"] = datetime.now().isoformat(timespec="seconds")
        meta["export_zip"] = str(zip_path)
        meta["next_action"] = "세무사에게 ZIP 패키지 전달 또는 추가자료 보완"

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    except Exception as e:
        write_log(case_dir.name, f"case_meta update failed: {e}")


def export_case(case_id, include_audio=True):
    case_dir = get_case_dir(case_id)
    export_dir = ensure_clean_export_dir(case_id)

    copied_files = []

    # Reports
    report_src_dir = case_dir / "06_reports"
    report_dst_dir = export_dir / "01_reports"
    for name in [
        "01_customer_summary.md",
        "02_office_check_report.md",
        "03_tax_accountant_review.md",
    ]:
        copy_file_if_exists(report_src_dir / name, report_dst_dir, copied_files, "report")
        
    # DOCX Reports
    docx_src_dir = case_dir / "06_reports_docx"
    docx_dst_dir = export_dir / "01_reports_docx"
    if docx_src_dir.exists():
        for name in [
            "01_customer_summary.docx",
            "02_office_check_report.docx",
            "03_tax_accountant_review.docx",
        ]:
            copy_file_if_exists(docx_src_dir / name, docx_dst_dir, copied_files, "report_docx")

    # Extract
    copy_file_if_exists(
        case_dir / "04_extract" / "tax_facts.json",
        export_dir / "02_extract",
        copied_files,
        "extract",
    )
    copy_file_if_exists(
        case_dir / "04_extract" / "acquisition_price_review.json",
        export_dir / "02_extract",
        copied_files,
        "acquisition_price_review",
    )
    copy_file_if_exists(
        case_dir / "04_extract" / "multi_asset_split_review.json",
        export_dir / "02_extract",
        copied_files,
        "multi_asset_split_review",
    )
    copy_file_if_exists(
        case_dir / "04_extract" / "regulated_area_check.json",
        export_dir / "02_extract",
        copied_files,
        "regulated_area_check",
    )
    copy_file_if_exists(
        case_dir / "04_extract" / "legal_basis_check.json",
        export_dir / "02_extract",
        copied_files,
        "legal_basis_check",
    )
    copy_file_if_exists(
        case_dir / "04_extract" / "case_risk_grade.json",
        export_dir / "02_extract",
        copied_files,
        "case_risk_grade",
    )
    
    # Consents
    print_forms_src_dir = case_dir / "09_print_forms"
    consents_dst_dir = export_dir / "02_consents"
    if print_forms_src_dir.exists():
        for name in [
            "10_client_truthful_disclosure_notice.docx",
            "11_tax_filing_delegation_and_identity_check.docx",
            "12_tax_accountant_fee_scope_agreement.docx",
            "13_final_tax_filing_confirmation.docx",
        ]:
            copy_file_if_exists(print_forms_src_dir / name, consents_dst_dir, copied_files, "consent")

    # Missing
    missing_src_dir = case_dir / "05_missing"
    missing_dst_dir = export_dir / "03_missing"
    for name in [
        "missing_items.md",
        "kakao_request_message.txt",
        "office_followup_checklist.md",
        "acquisition_price_missing_items.md",
        "multi_asset_missing_items.md",
    ]:
        copy_file_if_exists(missing_src_dir / name, missing_dst_dir, copied_files, "missing")

    # Transcript
    copy_file_if_exists(
        case_dir / "02_transcript" / "transcript.txt",
        export_dir / "04_transcript",
        copied_files,
        "transcript",
    )
    copy_file_if_exists(
        case_dir / "02_transcript" / "transcript_meta.json",
        export_dir / "04_transcript",
        copied_files,
        "transcript_meta",
    )

    # Documents
    copy_dir_files(
        case_dir / "03_documents",
        export_dir / "05_documents",
        copied_files,
        "document",
    )

    # Audio
    if include_audio:
        copy_dir_files(
            case_dir / "01_audio",
            export_dir / "06_audio",
            copied_files,
            "audio",
        )

    # Attachments
    attach_src_dir = case_dir / "11_attachments"
    if attach_src_dir.exists() and attach_src_dir.is_dir():
        attach_dst_dir = export_dir / "07_attachments"
        attach_dst_dir.mkdir(exist_ok=True)
        for cat_dir in attach_src_dir.iterdir():
            if cat_dir.is_dir():
                copy_dir_files(cat_dir, attach_dst_dir / cat_dir.name, copied_files, f"attachment_{cat_dir.name}")
            elif cat_dir.is_file():
                copy_file_if_exists(cat_dir, attach_dst_dir, copied_files, "attachment_file")

    manifest_path, manifest = write_manifest(
        export_dir,
        case_id,
        case_dir,
        copied_files,
        include_audio,
    )

    readme_path = write_readme(export_dir, case_id, manifest)
    copied_files.append({
        "label": "manifest",
        "source": "generated",
        "exported": str(manifest_path),
        "filename": manifest_path.name,
        "size_bytes": manifest_path.stat().st_size,
    })
    copied_files.append({
        "label": "readme",
        "source": "generated",
        "exported": str(readme_path),
        "filename": readme_path.name,
        "size_bytes": readme_path.stat().st_size,
    })

    # manifest에 generated 파일까지 반영하기 위해 한 번 더 저장
    write_manifest(export_dir, case_id, case_dir, copied_files, include_audio)

    zip_path = zip_export_dir(export_dir, case_id)
    update_case_meta(case_dir, zip_path)

    return export_dir, zip_path, copied_files


def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 세무사 전달용 사건 패키지 생성기")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="녹음파일을 export 패키지에서 제외"
    )

    args = parser.parse_args()

    case_id = args.case_id
    include_audio = not args.no_audio

    try:
        print("[START] 세무사 전달용 사건 패키지 생성 시작")
        print(f"[CASE_ID] {case_id}")
        print(f"[INCLUDE_AUDIO] {include_audio}")

        export_dir, zip_path, copied_files = export_case(case_id, include_audio=include_audio)

        write_log(case_id, f"export_created files={len(copied_files)} zip={zip_path}")

        print("[SUCCESS] 세무사 전달용 사건 패키지 생성 완료")
        print(f"[EXPORT_DIR] {export_dir}")
        print(f"[ZIP] {zip_path}")
        print(f"[FILE_COUNT] {len(copied_files)}")
        print("")
        print("[NEXT]")
        print("1. ZIP 파일을 세무사에게 전달하세요.")
        print("2. 개인정보가 포함되어 있으므로 전달 전 수신자를 반드시 확인하세요.")
        print("3. 녹음파일 제외가 필요하면 --no-audio 옵션으로 다시 생성하세요.")

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 세무사 전달용 사건 패키지 생성 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
