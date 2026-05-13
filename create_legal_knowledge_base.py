import json
import csv
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
LEGAL_DIR = BASE_DIR / "legal_knowledge"

TODAY = datetime.now().strftime("%Y-%m-%d")


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "checked_at",
                "category",
                "law_name",
                "source",
                "status",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def build_readme():
    return f"""
# TaxCaseManager Legal Knowledge Base

이 폴더는 TaxCaseManager가 양도세 사전진단 리포트를 만들 때 참고하는 법령 기준 DB입니다.

## 목적

- 양도소득세 관련 주요 법령 기준 정리
- 재개발·재건축/조합원입주권/분양권 관련 체크포인트 정리
- 조정대상지역 이력 DB와 연결되는 기준 정리
- 리포트 작성 시 법령 기준일과 공식 출처를 표시하기 위한 자료 관리

## 주의

이 폴더는 법령 원문 전체를 저장하는 곳이 아닙니다.  
공식 법령 사이트와 공고 자료를 기준으로 TaxCaseManager에서 필요한 체크포인트, 기준일, 출처 URL, 확인 상태만 관리합니다.

최종 세무 판단과 신고는 세무사 검토가 필요합니다.

## 마지막 생성일

{TODAY}
"""


def law_summary(law_name, purpose, key_checks):
    checks = "\n".join([f"- {x}" for x in key_checks])
    return f"""
# {law_name} 요약 기준

## TaxCaseManager 사용 목적

{purpose}

## 주요 확인 항목

{checks}

## 공식 출처

- 국가법령정보센터
- 국가법령정보 공동활용 API

## 관리 원칙

- 조문 번호와 시행일자는 공식 출처에서 확인한다.
- 법령 개정 가능성이 있으므로 리포트 작성 시 기준일을 표시한다.
- 본 요약은 사전진단 보조자료이며, 최종 판단은 세무사 검토가 필요하다.

## 마지막 확인일

{TODAY}

## 상태

초기 기준 파일 생성됨. 세부 조문번호는 후속 법령 검토 작업에서 보강 필요.
"""


def build_transfer_tax_rules():
    return {
        "schema_version": "1.0",
        "last_checked": TODAY,
        "description": "양도소득세 사전진단용 주요 체크포인트",
        "rules": [
            {
                "rule_id": "ONE_HOUSE_BASIC_REVIEW",
                "category": "1세대 1주택 비과세 가능성",
                "required_facts": [
                    "양도 부동산 종류",
                    "취득일",
                    "양도 예정일",
                    "보유기간",
                    "거주기간",
                    "본인 주택 수",
                    "배우자 주택 수",
                    "세대원 주택 수",
                    "분양권/입주권 보유 여부",
                    "상속주택 여부",
                    "조정대상지역 여부"
                ],
                "law_basis": [
                    {
                        "law_name": "소득세법",
                        "article": "세부 조문 후속 확인 필요",
                        "source": "law.go.kr"
                    },
                    {
                        "law_name": "소득세법 시행령",
                        "article": "세부 조문 후속 확인 필요",
                        "source": "law.go.kr"
                    }
                ],
                "report_warning": "1세대 1주택 비과세 가능성은 사전진단이며 최종 판단은 세무사 검토가 필요합니다."
            },
            {
                "rule_id": "ACQUISITION_PRICE_UNCLEAR",
                "category": "취득가액 불명확",
                "required_facts": [
                    "매수계약서 보유 여부",
                    "금융거래 내역",
                    "취득세 과세표준 자료",
                    "감정가액 검토 필요성",
                    "환산취득가액 검토 필요성",
                    "의제취득일 검토 필요성"
                ],
                "law_basis": [
                    {
                        "law_name": "소득세법",
                        "article": "취득가액 및 필요경비 관련 조문 후속 확인 필요",
                        "source": "law.go.kr"
                    }
                ],
                "tax_accountant_required": True,
                "report_warning": "취득가액이 불명확한 경우 임의 추정값을 확정값처럼 사용하지 않습니다."
            }
        ]
    }


def build_redevelopment_rules():
    return {
        "schema_version": "1.0",
        "last_checked": TODAY,
        "description": "재개발·재건축/조합원입주권/분양권 사건 체크포인트",
        "rules": [
            {
                "rule_id": "REDEVELOPMENT_RECONSTRUCTION_REVIEW",
                "category": "재개발·재건축 고위험 검토",
                "required_facts": [
                    "정비사업 종류",
                    "사업시행인가일",
                    "관리처분계획인가일",
                    "기존 주택 멸실일",
                    "조합원입주권 발생일",
                    "권리가액",
                    "분담금",
                    "청산금",
                    "신축주택 배정 수",
                    "관리처분인가일 당시 조정대상지역 여부"
                ],
                "law_basis": [
                    {
                        "law_name": "소득세법",
                        "purpose": "양도소득세 과세 및 비과세 검토",
                        "source": "law.go.kr"
                    },
                    {
                        "law_name": "소득세법 시행령",
                        "purpose": "입주권/분양권, 1세대 1주택, 거주요건 검토",
                        "source": "law.go.kr"
                    },
                    {
                        "law_name": "도시 및 주거환경정비법",
                        "purpose": "사업시행인가, 관리처분계획인가, 조합원입주권 사실관계 확인",
                        "source": "law.go.kr"
                    }
                ],
                "tax_accountant_required": True,
                "urban_renewal_expert_review_recommended": True,
                "report_warning": "재개발·재건축 사건은 세법과 도시정비법상 사실관계를 함께 확인해야 하며, 최종 판단은 세무사 검토가 필요합니다."
            }
        ]
    }


def build_residence_rules():
    return {
        "schema_version": "1.0",
        "last_checked": TODAY,
        "description": "거주요건 및 조정대상지역 관련 체크포인트",
        "rules": [
            {
                "rule_id": "REGULATED_AREA_RESIDENCE_REQUIREMENT",
                "category": "조정대상지역 및 거주요건",
                "required_facts": [
                    "취득일",
                    "관리처분계획인가일",
                    "권리 취득일",
                    "실제 거주기간",
                    "주민등록초본",
                    "조정대상지역 이력 DB 조회 결과"
                ],
                "system_modules": [
                    "regulated_area_history_check.py",
                    "regulated_area_history.csv"
                ],
                "report_warning": "조정대상지역 여부는 기준일에 따라 달라질 수 있으며, 세법상 효과는 세무사 검토가 필요합니다."
            }
        ]
    }


def build_multi_asset_rules():
    return {
        "schema_version": "1.0",
        "last_checked": TODAY,
        "description": "1주택에서 2개 이상 입주권/분양권/신축주택이 발생한 사건의 물건별 분리 검토 기준",
        "rules": [
            {
                "rule_id": "ONE_HOUSE_TO_MULTIPLE_RIGHTS",
                "category": "물건별 양도세 분리 검토",
                "trigger_conditions": [
                    "rights_count >= 2",
                    "new_units_count >= 2",
                    "asset_units length >= 2",
                    "one_house_to_multiple_rights = yes"
                ],
                "required_facts_per_asset": [
                    "물건별 양도 예정일",
                    "물건별 양도 예정가액",
                    "물건별 취득가액 배분",
                    "물건별 필요경비 배분",
                    "물건별 거주요건 관련 정보",
                    "양도 순서"
                ],
                "tax_accountant_required": True,
                "report_warning": "기존 1주택에서 2개 이상 권리 또는 신축주택이 발생한 경우 물건별 분리 검토가 필요합니다."
            }
        ]
    }


def build_regulated_area_reference():
    return f"""
# 조정대상지역 이력 DB 참고 문서

## 목적

TaxCaseManager는 양도세 사전진단 리포트 작성 시 조정대상지역 여부를 매번 확인합니다.

## 기준일

- 일반 주택: 취득일
- 재개발·재건축: 관리처분계획인가일 우선 확인
- 조합원입주권/분양권: 권리 취득일 또는 관리처분계획인가일 등 사안별 확인 필요

## 사용 파일

- data/regulated_area_history.csv
- data/regulated_area_notices.csv
- regulated_area_history_check.py
- update_regulated_area_history.py
- audit_regulated_area_coverage.py

## 판정 원칙

- YES: 기준일이 조정대상지역 ACTIVE 기간에 포함
- NO: 기준일 기준 해제 또는 미지정
- PARTIAL: 일부 지역 또는 택지지구만 해당
- UNKNOWN: 주소 또는 기준일 불명확

## 주의

조정대상지역 여부는 사전확인 자료이며, 기준일 적용과 세법상 효과는 세무사 검토가 필요합니다.

## 마지막 확인일

{TODAY}
"""


def build_status():
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "last_checked": TODAY,
        "status": "INITIAL_BASELINE",
        "official_sources": [
            "국가법령정보센터",
            "국가법령정보 공동활용 API",
            "국토교통부 행정규칙/공고"
        ],
        "laws": [
            {
                "name": "소득세법",
                "source": "law.go.kr",
                "status": "summary_created",
                "detail_article_check_required": True
            },
            {
                "name": "소득세법 시행령",
                "source": "law.go.kr",
                "status": "summary_created",
                "detail_article_check_required": True
            },
            {
                "name": "조세특례제한법",
                "source": "law.go.kr",
                "status": "summary_created",
                "detail_article_check_required": True
            },
            {
                "name": "도시 및 주거환경정비법",
                "source": "law.go.kr",
                "status": "summary_created",
                "detail_article_check_required": True
            },
            {
                "name": "도시 및 주거환경정비법 시행령",
                "source": "law.go.kr",
                "status": "summary_created",
                "detail_article_check_required": True
            }
        ],
        "regulated_area_history_db": {
            "status": "validated",
            "note": "regulated_area_history.csv 및 audit 결과를 별도 확인"
        },
        "warning": "본 법령 기준 DB는 사전진단용이며 최종 세무 판단은 세무사 검토가 필요합니다."
    }


def main():
    (LEGAL_DIR / "laws").mkdir(parents=True, exist_ok=True)
    (LEGAL_DIR / "rules").mkdir(parents=True, exist_ok=True)
    (LEGAL_DIR / "notices").mkdir(parents=True, exist_ok=True)
    (LEGAL_DIR / "versions").mkdir(parents=True, exist_ok=True)

    write_text(LEGAL_DIR / "README.md", build_readme())

    write_text(
        LEGAL_DIR / "laws" / "income_tax_act_summary.md",
        law_summary(
            "소득세법",
            "양도소득세 과세, 비과세, 취득가액, 필요경비 등 기본 세법 판단의 기준으로 사용합니다.",
            [
                "양도소득세 과세대상",
                "1세대 1주택 비과세 가능성",
                "취득가액 및 필요경비",
                "장기보유특별공제",
                "세율 및 중과 가능성",
            ],
        ),
    )

    write_text(
        LEGAL_DIR / "laws" / "income_tax_enforcement_decree_summary.md",
        law_summary(
            "소득세법 시행령",
            "1세대 1주택 요건, 보유기간, 거주기간, 조정대상지역 관련 세부 판단을 위한 기준으로 사용합니다.",
            [
                "1세대 1주택 요건",
                "보유기간 및 거주기간",
                "조정대상지역 취득 주택 거주요건",
                "조합원입주권/분양권 관련 검토",
            ],
        ),
    )

    write_text(
        LEGAL_DIR / "laws" / "special_tax_treatment_control_act_summary.md",
        law_summary(
            "조세특례제한법",
            "특례, 감면, 장기임대주택 등 특수한 양도세 검토가 필요한 경우 참고합니다.",
            [
                "양도세 감면/특례 가능성",
                "장기임대주택 관련 특례",
                "농어촌주택 등 특수 케이스",
            ],
        ),
    )

    write_text(
        LEGAL_DIR / "laws" / "urban_renewal_act_summary.md",
        law_summary(
            "도시 및 주거환경정비법",
            "재개발·재건축 사건에서 사업시행인가, 관리처분계획인가, 조합원 지위, 입주권 발생 사실관계를 확인하는 기준으로 사용합니다.",
            [
                "정비사업 종류",
                "사업시행인가일",
                "관리처분계획인가일",
                "조합원입주권 발생 여부",
                "권리가액/분담금/청산금",
                "신축주택 배정 수",
            ],
        ),
    )

    write_text(
        LEGAL_DIR / "laws" / "urban_renewal_enforcement_decree_summary.md",
        law_summary(
            "도시 및 주거환경정비법 시행령",
            "도시정비법상 세부 절차와 정비사업 관련 사실관계 확인에 참고합니다.",
            [
                "관리처분계획 관련 세부 사항",
                "정비사업 절차",
                "조합원 관련 세부 기준",
                "정비사업 서류 확인 필요 항목",
            ],
        ),
    )

    write_json(LEGAL_DIR / "rules" / "transfer_tax_rule_checkpoints.json", build_transfer_tax_rules())
    write_json(LEGAL_DIR / "rules" / "redevelopment_reconstruction_checkpoints.json", build_redevelopment_rules())
    write_json(LEGAL_DIR / "rules" / "residence_requirement_checkpoints.json", build_residence_rules())
    write_json(LEGAL_DIR / "rules" / "multi_asset_split_checkpoints.json", build_multi_asset_rules())

    write_text(LEGAL_DIR / "notices" / "regulated_area_reference.md", build_regulated_area_reference())

    write_csv(
        LEGAL_DIR / "versions" / "legal_update_log.csv",
        [
            {
                "checked_at": TODAY,
                "category": "INITIAL_BASELINE",
                "law_name": "TaxCaseManager legal_knowledge",
                "source": "local",
                "status": "created",
                "note": "법령 기준 DB 1차 구조 생성",
            }
        ],
    )

    write_json(LEGAL_DIR / "versions" / "legal_basis_status.json", build_status())

    print("[SUCCESS] legal_knowledge 법령 기준 DB 1차 구축 완료")
    print(f"[DIR] {LEGAL_DIR}")


if __name__ == "__main__":
    main()
