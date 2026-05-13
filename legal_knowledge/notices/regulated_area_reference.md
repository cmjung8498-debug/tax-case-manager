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

2026-05-13
