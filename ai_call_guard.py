import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"

POLICY_PATH = CONFIG_DIR / "ai_policy.json"


DEFAULT_POLICY = {
    "default_ai_enabled": False,
    "allowed_ai_tasks": {
        "transcription": True,
        "ai_fact_extract": False,
        "tax_law_rag": False,
        "report_generation": False
    },
    "risk_based_ai_policy": {
        "GREEN": False,
        "YELLOW": False,
        "ORANGE": True,
        "RED": True
    },
    "cache_required": True,
    "log_required": True,
    "max_audio_minutes_per_case": 30,
    "max_ai_calls_per_case": 3,
    "default_report_generation": "template_only"
}


def ensure_policy_file():
    CONFIG_DIR.mkdir(exist_ok=True)

    if not POLICY_PATH.exists():
        with open(POLICY_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_POLICY, f, ensure_ascii=False, indent=2)

    return POLICY_PATH


def load_policy():
    ensure_policy_file()

    try:
        with open(POLICY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_POLICY


def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir


def get_cost_dir(case_id):
    case_dir = get_case_dir(case_id)
    cost_dir = case_dir / "08_cost"
    cost_dir.mkdir(exist_ok=True)
    return cost_dir


def read_json_if_exists(path):
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_case_risk_level(case_id):
    case_dir = get_case_dir(case_id)

    tax_data = read_json_if_exists(case_dir / "04_extract" / "tax_facts.json")
    meta = read_json_if_exists(case_dir / "case_meta.json")

    return (
        tax_data.get("risk_level")
        or meta.get("risk_level")
        or "UNKNOWN"
    )


def get_usage(case_id):
    cost_dir = get_cost_dir(case_id)
    usage_path = cost_dir / "api_usage.json"

    if not usage_path.exists():
        return {
            "case_id": case_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "calls": []
        }

    try:
        with open(usage_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "case_id": case_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "calls": []
        }


def save_usage(case_id, usage):
    cost_dir = get_cost_dir(case_id)
    usage_path = cost_dir / "api_usage.json"

    usage["updated_at"] = datetime.now().isoformat(timespec="seconds")

    with open(usage_path, "w", encoding="utf-8") as f:
        json.dump(usage, f, ensure_ascii=False, indent=2)

    return usage_path


def count_ai_calls(case_id):
    usage = get_usage(case_id)
    return len(usage.get("calls", []))


def has_cached_output(case_id, task_name, output_path):
    if not output_path:
        return False

    path = Path(output_path)
    return path.exists() and path.stat().st_size > 0


def is_task_allowed_by_policy(task_name, case_id=None):
    policy = load_policy()

    allowed_tasks = policy.get("allowed_ai_tasks", {})
    task_allowed = bool(allowed_tasks.get(task_name, False))

    if not task_allowed:
        return False, f"AI task disabled by policy: {task_name}"

    if case_id:
        max_calls = int(policy.get("max_ai_calls_per_case", 3))
        current_calls = count_ai_calls(case_id)

        if current_calls >= max_calls:
            return False, f"AI call limit exceeded: {current_calls}/{max_calls}"

    return True, "allowed"


def should_use_ai_for_risk(case_id):
    policy = load_policy()
    risk_level = get_case_risk_level(case_id)

    risk_policy = policy.get("risk_based_ai_policy", {})
    return bool(risk_policy.get(risk_level, False)), risk_level


def require_ai_permission(task_name, case_id=None, output_path=None):
    policy = load_policy()

    if policy.get("cache_required", True) and output_path:
        if has_cached_output(case_id, task_name, output_path):
            return {
                "allowed": False,
                "reason": "cached_output_exists",
                "task_name": task_name,
                "case_id": case_id,
                "output_path": str(output_path)
            }

    allowed, reason = is_task_allowed_by_policy(task_name, case_id=case_id)

    return {
        "allowed": allowed,
        "reason": reason,
        "task_name": task_name,
        "case_id": case_id,
        "output_path": str(output_path) if output_path else ""
    }


def log_ai_call(case_id, task_name, model, input_ref="", output_ref="", status="SUCCESS", meta=None):
    meta = meta or {}

    usage = get_usage(case_id)

    call = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "task_name": task_name,
        "model": model,
        "input_ref": str(input_ref),
        "output_ref": str(output_ref),
        "status": status,
        "meta": meta
    }

    usage.setdefault("calls", []).append(call)
    usage_path = save_usage(case_id, usage)

    LOGS_DIR.mkdir(exist_ok=True)
    global_log = LOGS_DIR / "ai_usage_log.txt"

    with open(global_log, "a", encoding="utf-8") as f:
        f.write(
            f"[{call['time']}] [{case_id}] task={task_name} model={model} "
            f"status={status} output={output_ref}\n"
        )

    write_usage_summary(case_id)

    return usage_path


def write_usage_summary(case_id):
    usage = get_usage(case_id)
    cost_dir = get_cost_dir(case_id)
    summary_path = cost_dir / "api_usage_summary.md"

    calls = usage.get("calls", [])

    lines = []
    lines.append(f"# {case_id} API 사용 요약")
    lines.append("")
    lines.append(f"- API 호출 수: {len(calls)}")
    lines.append("")

    if not calls:
        lines.append("- 현재 기록된 API 호출 없음")
    else:
        lines.append("| 시간 | 작업 | 모델 | 상태 | 출력 |")
        lines.append("|---|---|---|---|---|")
        for call in calls:
            lines.append(
                f"| {call.get('time', '')} "
                f"| {call.get('task_name', '')} "
                f"| {call.get('model', '')} "
                f"| {call.get('status', '')} "
                f"| {call.get('output_ref', '')} |"
            )

    lines.append("")
    lines.append("## 운영 원칙")
    lines.append("")
    lines.append("- AI는 전사, 비정형 추출 보조, 고위험 사건의 세법 자료 검색에만 사용한다.")
    lines.append("- 리포트 생성은 템플릿 기반을 원칙으로 한다.")
    lines.append("- 같은 사건의 같은 결과물이 있으면 재호출하지 않는다.")
    lines.append("- OPENAI_API_KEY는 코드에 저장하지 않는다.")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return summary_path
