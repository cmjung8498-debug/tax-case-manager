import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"


FIELD_LABELS = {
    "property_address": "매도 예정 부동산 주소",
    "acquired_date": "취득일",
    "acquired_price": "취득가액",
    "sale_expected_date": "양도 예정일",
    "sale_expected_price": "양도 예정가액",
    "current_house_count": "현재 보유 주택 수",
    "spouse_house_owned": "배우자 명의 주택 보유 여부",
    "household_member_house_owned": "세대원 주택 보유 여부",
    "residence_period": "실제 거주기간",
    "inherited_house": "상속주택 여부",
    "presale_right_or_occupancy_right": "분양권/입주권 여부",
    "necessary_expense_evidence": "필요경비 증빙자료",
}


def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "report_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")


def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir


def read_json(path):
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_json_optional(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def yn(value):
    return "Y" if value else "N"


def build_acquisition_customer_section(acq_data):
    if not acq_data:
        return "## 취득가액 확인 상태\n\n- 취득가액 검토 모듈 미실행\n"

    grade = acq_data.get("confidence_grade", "미확인")
    reason = acq_data.get("confidence_reason", "미확인")
    missing = acq_data.get("missing_core_evidence", [])
    tax_required = acq_data.get("tax_accountant_required", False)

    lines = []
    lines.append("## 취득가액 확인 상태")
    lines.append("")
    lines.append("현재 취득가액은 일부 확인 가능성이 있으나, 최종 확정 전 추가 증빙 확인이 필요합니다.")
    lines.append("")
    lines.append(f"- 취득가액 신뢰도: {grade}")
    lines.append(f"- 사유: {reason}")
    lines.append("- 추가 확인 필요 자료:")
    if missing:
        for item in missing:
            lines.append(f"  - {item}")
    else:
        lines.append("  - 현재 추가 확인 자료 없음")
    lines.append("")
    lines.append("※ 취득가액은 양도세 계산에 큰 영향을 주므로, 최종 판단은 세무사 검토가 필요합니다.")
    return "\n".join(lines)


def build_acquisition_office_section(acq_data):
    if not acq_data:
        return "## 취득가액 검토 체크\n\n- 취득가액 검토 모듈 미실행\n"

    grade = acq_data.get("confidence_grade", "미확인")
    tax_required = acq_data.get("tax_accountant_required", False)
    replace_req = acq_data.get("needs_replacement_review", False)
    partial = acq_data.get("partial_evidence", [])
    missing = acq_data.get("missing_core_evidence", [])
    
    replace_text = "조건부" if not replace_req else "Y"

    lines = []
    lines.append("## 취득가액 검토 체크")
    lines.append("")
    lines.append(f"- 취득가액 신뢰도: {grade}")
    lines.append(f"- 세무사 필수 검토: {yn(tax_required)}")
    lines.append(f"- 대체 취득가액 검토 필요: {replace_text}")
    lines.append("- 일부 확인 자료:")
    if partial:
        for item in partial:
            lines.append(f"  - {item}")
    else:
        lines.append("  - 없음")
    lines.append("- 부족한 핵심 증빙:")
    if missing:
        for item in missing:
            lines.append(f"  - {item}")
    else:
        lines.append("  - 없음")
    lines.append("")
    lines.append("부동산 사무실 조치:")
    lines.append("- 고객에게 매수계약서 보유 여부를 재확인한다.")
    lines.append("- 취득 당시 계좌이체 내역 또는 대금 지급 자료가 있는지 확인한다.")
    lines.append("- 취득세 납부자료에 과세표준 또는 취득가액이 표시되는지 확인한다.")
    lines.append("- 위 자료가 없으면 세무사에게 대체 취득가액 검토 필요 사건으로 전달한다.")
    return "\n".join(lines)


def build_acquisition_tax_section(acq_data):
    if not acq_data:
        return "## 취득가액 불명확 및 대체 취득가액 검토\n\n- 취득가액 검토 모듈 미실행\n"

    grade = acq_data.get("confidence_grade", "미확인")
    reason = acq_data.get("confidence_reason", "미확인")
    tax_required = acq_data.get("tax_accountant_required", False)
    replace_req = acq_data.get("needs_replacement_review", False)
    
    replace_text = "conditional" if not replace_req else "Y"

    lines = []
    lines.append("## 취득가액 불명확 및 대체 취득가액 검토")
    lines.append("")
    lines.append("본 사건은 취득가액 관련 핵심 증빙이 완전히 확인되지 않았습니다.")
    lines.append("")
    lines.append(f"- 취득가액 신뢰도: {grade}")
    lines.append(f"- 판정 사유: {reason}")
    lines.append(f"- 세무사 필수 검토: {yn(tax_required)}")
    lines.append(f"- 대체 취득가액 검토 필요 여부: {replace_text}")
    lines.append("")
    lines.append("검토 필요:")
    lines.append("- 실제 취득가액 인정 가능 여부")
    lines.append("- 매수계약서/금융자료/취득세 과세표준 자료 확인")
    lines.append("- 실제 취득가액 확인 불가 시 매매사례가액 검토")
    lines.append("- 감정가액 검토")
    lines.append("- 환산취득가액 검토")
    lines.append("- 오래된 취득 건이면 의제취득일/기준시가/토지등급 자료 확인")
    lines.append("")
    lines.append("주의:")
    lines.append("본 리포트는 취득가액을 확정하지 않으며, 최종 취득가액 산정은 세무사 검토가 필요합니다.")
    return "\n".join(lines)


def build_redev_customer_section(multi_asset_data):
    if not multi_asset_data or not multi_asset_data.get("multi_asset_review_required"):
        return ""

    return """## 재개발·재건축/입주권·분양권 추가 확인

본 사건은 재개발·재건축 또는 조합원입주권/분양권 관련 가능성이 있어
일반 주택 양도세 계산만으로 확정 판단하기 어렵습니다.

특히 기존 1주택에서 2개 이상의 입주권/분양권 또는 신축 아파트가 발생한 경우,
각 물건별 양도 예정일, 양도가액, 취득가액 배분, 필요경비 배분, 양도 순서를
별도로 확인해야 합니다.

이 사건은 세무사 검토가 필요할 수 있습니다."""


def build_redev_office_section(multi_asset_data):
    if not multi_asset_data or not multi_asset_data.get("multi_asset_review_required"):
        return ""

    return """## 재개발·재건축 고위험 체크

- 관리처분계획인가일 확인 필요
- 관리처분인가일 당시 조정대상지역 여부 확인 필요
- 기존 1주택이 2개 권리/2개 신축 아파트로 전환되었는지 확인 필요
- 각 물건별 양도예정가액 확인 필요
- 각 물건별 취득가액/필요경비 배분 확인 필요
- 양도 순서 확인 필요
- 실거주 요건 검토 필요
- 세무사 필수 검토 여부: Y"""


def build_redev_tax_section(multi_asset_data):
    if not multi_asset_data or not multi_asset_data.get("multi_asset_review_required"):
        return ""

    return """## 도시 및 주거환경정비법상 확인사항

본 사건은 단독주택이 재건축사업을 거쳐 2개의 아파트로 전환된 사건입니다.
따라서 양도소득세 판단과 별도로 도시 및 주거환경정비법상 정비사업 사실관계를 확인해야 합니다.

확인할 도정법상 사실관계:
- 정비사업 종류
- 조합설립인가일
- 사업시행인가일
- 관리처분계획인가일
- 권리가액
- 추가분담금
- 청산금 여부
- 신축주택 배정 수
- 준공검사일
- 이전고시일
- 개별등기일

도정법상 사실관계는 세법상 취득시기, 조합원입주권 전환 시점, 물건별 취득가액 배분, 양도차익 구분에 영향을 줄 수 있습니다."""


def build_regulated_area_customer_section(regulated_area_data):
    if not regulated_area_data:
        return ""
    
    return f"""## 조정대상지역 여부 확인

본 사건은 기준일 당시 조정대상지역 여부 확인이 필요한 사건입니다.

- 기준일 유형: {regulated_area_data.get("basis_date_type", "")}
- 기준일: {regulated_area_data.get("basis_date", "")}
- 대상 지역: {regulated_area_data.get("region", "")}
- 조정대상지역 여부: {regulated_area_data.get("is_adjustment_target_area", "")}
- 확인 신뢰도: {regulated_area_data.get("confidence", "")}

조정대상지역 여부는 거주요건, 비과세 판단, 재개발·재건축 검토에 영향을 줄 수 있으므로 최종 판단은 세무사 검토가 필요합니다."""


def build_regulated_area_office_section(regulated_area_data):
    if not regulated_area_data:
        return ""

    return f"""## 조정대상지역 확인 체크

- 관리처분계획인가일 또는 취득일 확인 필요
- 주소 기준 시군구 확인 필요
- 공식 조정대상지역 이력 DB 조회 결과 확인
- 불명확 시 세무사 필수 검토
- 기준일: {regulated_area_data.get("basis_date", "")}
- 판정결과: {regulated_area_data.get("is_adjustment_target_area", "")} ({regulated_area_data.get("confidence", "")})"""


def build_regulated_area_tax_section(regulated_area_data):
    if not regulated_area_data:
        return ""

    return """## 조정대상지역 기준일별 확인

본 사건은 단일 기준일만으로 조정대상지역 여부를 판단하기 어렵습니다.
다음 기준일별로 부산 연제구의 조정대상지역 여부를 확인해야 합니다.

- 최초 취득일: 2001-03-21
- 관리처분계획인가일: 2015년 정확한 일자 필요
- 준공검사일: 2018-10
- 개별등기일: 2019년 정확한 일자 필요
- 양도 예정일: 2026년 10월 이전 또는 2026년 11월 이후

각 기준일별 조정대상지역 여부는 거주요건, 비과세 판단, 장기임대주택 특례 판단에 영향을 줄 수 있습니다."""


def build_legal_basis_common_section(legal_basis_data):
    if not legal_basis_data:
        return ""
    
    db_status = legal_basis_data.get("legal_basis_status", "미확인")
    last_checked = legal_basis_data.get("legal_basis_last_checked", "미확인")
    reg_db = legal_basis_data.get("regulated_area_db", {})
    ok_count = reg_db.get("ok_count", 0)
    partial_count = reg_db.get("partial_only_count", 0)
    missing_count = reg_db.get("missing_count", 0)
    no_src_count = reg_db.get("no_official_source_count", 0)
    
    laws = legal_basis_data.get("laws", [])
    detail_req = any(law.get("detail_article_check_required") for law in laws)
    detail_req_str = "Y" if detail_req else "N"

    return f"""## 법령 기준 및 공식 DB 확인

본 리포트는 TaxCaseManager 법령 기준 DB와 조정대상지역 이력 DB를 기준으로 작성된 사전진단 자료입니다.

- 법령 기준 DB 상태: {db_status}
- 법령 마지막 확인일: {last_checked}
- 조정대상지역 DB OK 건수: {ok_count}
- 조정대상지역 DB PARTIAL 건수: {partial_count}
- 조정대상지역 DB MISSING 건수: {missing_count}
- 조정대상지역 DB NO_OFFICIAL_SOURCE 건수: {no_src_count}
- 법령 세부 조문 추가 확인 필요 여부: {detail_req_str}

주의:
세법 및 도시정비 관련 법령은 수시로 개정될 수 있으므로, 최종 세무 판단 및 신고는 세무사 검토 후 진행해야 합니다."""


def build_legal_basis_tax_section(legal_basis_data):
    if not legal_basis_data:
        return ""
        
    laws = legal_basis_data.get("laws", [])
    law_lines = "\n".join(f"- {law.get('name')}" for law in laws)
    
    return f"""## 세무사용 법령 기준 확인

참조 법령 기준 DB:
{law_lines}

본 시스템의 법령 DB는 사전진단 체크포인트용이며, 세부 조문 적용과 최신 개정 여부는 세무사 검토가 필요합니다."""


def build_40py_section():
    return """## 40평 아파트 거주주택 비과세 검토

25평 아파트가 세법상 장기임대주택 요건을 충족하고,
40평 아파트가 거주주택 요건을 충족하며,
양도 당시 세대 내 다른 일반주택이 없고,
40평 양도가액이 12억 원 이하라는 전제가 사실이라면,
40평 아파트는 장기임대주택 보유자의 거주주택 비과세 적용 대상입니다.

본 사건의 40평 예상 양도가액은 10억 원으로, 현행 고가주택 기준 12억 원 이하입니다.

확인할 전제:
- 25평 장기임대주택 요건 충족 여부
- 40평 거주주택 요건 충족 여부
- 기존 단독주택 거주기간 통산 가능 여부
- 양도 당시 세대 내 다른 일반주택 여부
- 부산 연제구 기준일별 조정대상지역 여부

세무사 최종 확인 쟁점:
- 재건축 전 종전 단독주택 거주기간을 40평 거주주택 요건에 반영할 수 있는지
- 관리처분인가일, 준공일, 개별등기일, 양도일 중 어느 기준일을 적용할지"""


def build_25py_section():
    return """## 25평 장기임대주택 양도세 검토

25평 아파트가 민간임대주택 등록, 세무서 사업자등록, 8년 계속임대, 임대료 증액 제한 등 장기임대주택 특례 요건을 충족하고,
2026년 11월 이후 양도한다는 전제가 사실이라면,
25평 아파트는 장기임대주택 장기보유특별공제 50% 특례 적용 대상입니다.

현재 입력자료 기준 25평을 6.5억 원에 양도하고 8년 장기임대주택 특례를 적용하는 경우,
부부 합산 개략 양도세는 약 5,850만 원 수준으로 계산됩니다.

확인할 전제:
- 임대사업자 등록일
- 세무서 사업자등록 여부
- 임대개시일
- 8년 계속임대 충족일
- 임대료 증액 제한 준수 여부
- 임대차계약 신고 이력
- 등록말소 여부
- 공동명의 각각의 특례 적용 가능 여부"""


def format_value(value):
    if value is None:
        return "미확인"

    if value == "":
        return "미확인"

    if value == "unknown":
        return "미확인"

    if value == "yes":
        return "있음"

    if value == "no":
        return "없음"

    if isinstance(value, list):
        if not value:
            return "미확인"
        return ", ".join(str(v) for v in value)

    return str(value)


def risk_description(risk_level):
    mapping = {
        "GREEN": "기초 사실관계가 비교적 명확한 사건입니다.",
        "YELLOW": "일부 누락자료가 있어 보완 후 판단이 필요합니다.",
        "ORANGE": "주택 수, 세대원, 고가주택, 권리관계 등 주요 쟁점 확인이 필요합니다.",
        "RED": "누락자료가 많거나 고위험 쟁점이 있어 세무사 검토가 필수입니다.",
    }
    return mapping.get(risk_level, "위험등급 설명 미확정")


def build_fact_table(facts):
    lines = []
    lines.append("| 항목 | 내용 |")
    lines.append("|---|---|")

    for key, label in FIELD_LABELS.items():
        value = facts.get(key)
        lines.append(f"| {label} | {format_value(value)} |")

    return "\n".join(lines)


def build_missing_section(missing_items):
    if not missing_items:
        return "- 현재 1차 필수항목 기준 누락 없음"

    return "\n".join(f"- {item}" for item in missing_items)


def build_evidence_section(facts):
    sentences = facts.get("raw_evidence_sentences", [])

    if not sentences:
        return "- 상담 원문 근거 문장 없음"

    lines = []
    for sentence in sentences[:20]:
        lines.append(f"- {sentence}")

    return "\n".join(lines)


def build_customer_report(case_id, meta, tax_data, acq_data, multi_asset_data, regulated_area_data, legal_basis_data):
    facts = tax_data.get("facts", {})
    missing_items = tax_data.get("missing_items", [])
    case_type = tax_data.get("case_type", "미확정")
    risk_level = tax_data.get("risk_level", "미확정")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# 고객용 양도세 사전검토 요약 리포트

## 1. 사건 기본정보

- 사건번호: {case_id}
- 생성일시: {now}
- 부동산 사무실: {meta.get("real_estate_office", "") or "미입력"}
- 담당자: {meta.get("manager_name", "") or "미입력"}
- 고객명: {meta.get("client_name", "") or "미입력"}
- 매도 예정 부동산: {format_value(facts.get("property_address"))}

## 2. 1차 사건유형

- 사건유형 추정: {case_type}
- 위험등급: {risk_level}
- 등급 설명: {risk_description(risk_level)}

## 3. 현재까지 확인된 주요 내용

{build_fact_table(facts)}

## 4. 추가 확인이 필요한 내용

{build_missing_section(missing_items)}

{build_acquisition_customer_section(acq_data)}

{build_redev_customer_section(multi_asset_data)}

{build_regulated_area_customer_section(regulated_area_data)}

{build_legal_basis_common_section(legal_basis_data)}

{build_40py_section()}

{build_25py_section()}

## 5. 안내

본 리포트는 고객이 제공한 상담 내용과 자료를 바탕으로 작성된 1차 사전검토 자료입니다.

이 문서는 양도소득세 확정 판단 또는 신고서가 아닙니다.  
최종 세무 판단은 증빙자료 확인 후 세무사 검토를 통해 확정되어야 합니다.
"""


def build_office_report(case_id, meta, tax_data, acq_data, multi_asset_data, regulated_area_data, legal_basis_data):
    facts = tax_data.get("facts", {})
    missing_items = tax_data.get("missing_items", [])
    case_type = tax_data.get("case_type", "미확정")
    risk_level = tax_data.get("risk_level", "미확정")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# 부동산 사무실 내부 확인 리포트

## 1. 사건 관리 정보

- 사건번호: {case_id}
- 생성일시: {now}
- 사건상태: {meta.get("status", "미확인")}
- 부동산 사무실: {meta.get("real_estate_office", "") or "미입력"}
- 담당자: {meta.get("manager_name", "") or "미입력"}
- 고객명: {meta.get("client_name", "") or "미입력"}
- 고객 연락처: {meta.get("client_phone", "") or "미입력"}
- 물건주소: {format_value(facts.get("property_address"))}

## 2. AI/룰 기반 1차 분류

- 사건유형 추정: {case_type}
- 위험등급: {risk_level}
- 등급 설명: {risk_description(risk_level)}
- 추출방식: {tax_data.get("extract_method", "미확인")}

## 3. 사실관계 확인표

{build_fact_table(facts)}

## 4. 부동산 사무실 보완 요청 항목

{build_missing_section(missing_items)}

{build_acquisition_office_section(acq_data)}

{build_redev_office_section(multi_asset_data)}

{build_regulated_area_office_section(regulated_area_data)}

{build_legal_basis_common_section(legal_basis_data)}

{build_40py_section()}

{build_25py_section()}

## 5. 상담 원문 근거 문장 후보

{build_evidence_section(facts)}

## 6. 내부 주의사항

- 부동산 사무실은 세무 판단을 확정하지 않는다.
- 고객에게 부족자료를 재확인하고 증빙을 추가 수집한다.
- 미확인 항목이 남아 있으면 세무사에게 확정 판단을 요청하지 않는다.
- 위험등급 ORANGE 이상은 세무사 검토 대상으로 분류한다.
"""


def build_tax_accountant_report(case_id, meta, tax_data, acq_data, multi_asset_data, regulated_area_data, legal_basis_data):
    facts = tax_data.get("facts", {})
    missing_items = tax_data.get("missing_items", [])
    case_type = tax_data.get("case_type", "미확정")
    risk_level = tax_data.get("risk_level", "미확정")
    verdict = tax_data.get("verdict", "")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# 세무사 검토 요청 리포트

## 1. 검토 요청 개요

- 사건번호: {case_id}
- 생성일시: {now}
- 사건유형 추정: {case_type}
- 위험등급: {risk_level}
- 등급 설명: {risk_description(risk_level)}
- 현재 판정: {verdict}

## 2. 의뢰 경로

- 부동산 사무실: {meta.get("real_estate_office", "") or "미입력"}
- 담당자: {meta.get("manager_name", "") or "미입력"}
- 고객명: {meta.get("client_name", "") or "미입력"}
- 고객 연락처: {meta.get("client_phone", "") or "미입력"}

## 3. 사실관계 요약

{build_fact_table(facts)}

## 4. 세무사 확인 필요 쟁점

{build_missing_section(missing_items)}

{build_acquisition_tax_section(acq_data)}

{build_redev_tax_section(multi_asset_data)}

{build_regulated_area_tax_section(regulated_area_data)}

{build_legal_basis_common_section(legal_basis_data)}

{build_legal_basis_tax_section(legal_basis_data)}

{build_40py_section()}

{build_25py_section()}

## 5. 검토 포인트

- 1세대 1주택 비과세 가능 여부
- 양도가액 12억 초과 고가주택 과세 여부
- 세대 기준 주택 수 확인
- 배우자 및 세대원 주택 보유 여부
- 실제 거주기간 및 증빙 가능 여부
- 분양권/입주권/상속주택 포함 여부
- 필요경비 인정 가능 증빙 여부
- 최종 양도세 신고 필요 여부

## 6. 상담 원문 근거 문장 후보

{build_evidence_section(facts)}

## 7. 세무사 회신란

아래 항목을 검토 후 회신해 주십시오.

| 항목 | 세무사 검토 의견 |
|---|---|
| 비과세 가능성 |  |
| 과세 가능성 |  |
| 추가 필요서류 |  |
| 신고 필요 여부 |  |
| 예상 주요 리스크 |  |
| 최종 의견 |  |

## 8. 주의 문구

본 리포트는 고객 진술 및 제출자료를 기반으로 한 사건 정리 자료입니다.  
본 문서 자체는 세무 판단 확정 또는 신고 대행 결과물이 아니며, 최종 판단은 세무사의 검토 의견에 따릅니다.
"""


def write_reports(case_dir, case_id, meta, tax_data, acq_data, multi_asset_data, regulated_area_data, legal_basis_data):
    report_dir = case_dir / "06_reports"
    report_dir.mkdir(exist_ok=True)

    customer_path = report_dir / "01_customer_summary.md"
    office_path = report_dir / "02_office_check_report.md"
    tax_path = report_dir / "03_tax_accountant_review.md"

    customer_report = build_customer_report(case_id, meta, tax_data, acq_data, multi_asset_data, regulated_area_data, legal_basis_data)
    office_report = build_office_report(case_id, meta, tax_data, acq_data, multi_asset_data, regulated_area_data, legal_basis_data)
    tax_report = build_tax_accountant_report(case_id, meta, tax_data, acq_data, multi_asset_data, regulated_area_data, legal_basis_data)

    with open(customer_path, "w", encoding="utf-8") as f:
        f.write(customer_report)

    with open(office_path, "w", encoding="utf-8") as f:
        f.write(office_report)

    with open(tax_path, "w", encoding="utf-8") as f:
        f.write(tax_report)

    return customer_path, office_path, tax_path


def update_case_meta(case_dir):
    meta_path = case_dir / "case_meta.json"

    if not meta_path.exists():
        return

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        meta["status"] = "04_REPORTED"
        meta["reported_at"] = datetime.now().isoformat(timespec="seconds")
        meta["next_action"] = "리포트 검토 후 누락자료 보완 또는 세무사 검토 요청"

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_log(case_dir.name, f"case_meta update failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 리포트 생성기")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    args = parser.parse_args()

    case_id = args.case_id

    try:
        case_dir = get_case_dir(case_id)
        meta_path = case_dir / "case_meta.json"
        tax_json_path = case_dir / "04_extract" / "tax_facts.json"

        print("[START] 리포트 생성 시작")
        print(f"[CASE_ID] {case_id}")

        meta = read_json(meta_path)
        tax_data = read_json(tax_json_path)

        acq_json_path = case_dir / "04_extract" / "acquisition_price_review.json"
        acq_data = read_json_optional(acq_json_path)

        multi_asset_path = case_dir / "04_extract" / "multi_asset_split_review.json"
        multi_asset_data = read_json_optional(multi_asset_path)

        regulated_area_path = case_dir / "04_extract" / "regulated_area_check.json"
        regulated_area_data = read_json_optional(regulated_area_path)
        
        legal_basis_path = case_dir / "04_extract" / "legal_basis_check.json"
        legal_basis_data = read_json_optional(legal_basis_path)

        customer_path, office_path, tax_path = write_reports(case_dir, case_id, meta, tax_data, acq_data, multi_asset_data, regulated_area_data, legal_basis_data)
        update_case_meta(case_dir)

        write_log(case_id, f"reports_created customer={customer_path.name} office={office_path.name} tax={tax_path.name}")

        print("[SUCCESS] 리포트 생성 완료")
        print(f"[CUSTOMER] {customer_path}")
        print(f"[OFFICE] {office_path}")
        print(f"[TAX_ACCOUNTANT] {tax_path}")
        print("")
        print("[NEXT]")
        print("1. 02_office_check_report.md를 확인하여 누락자료를 고객에게 보완 요청하세요.")
        print("2. 03_tax_accountant_review.md는 세무사 검토 요청용입니다.")
        print("3. 다음 단계는 export_case_bundle.py 또는 PDF 변환 기능입니다.")

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 리포트 생성 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
