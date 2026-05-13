import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from ai_call_guard import require_ai_permission, log_ai_call

BASE_DIR = Path(r"C:\TaxCaseManager")
CASES_DIR = BASE_DIR / "cases"
LOGS_DIR = BASE_DIR / "logs"

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".amr"}

# 안정성 우선 1차 모델.
# 필요 시 gpt-4o-transcribe 또는 gpt-4o-mini-transcribe로 교체 가능.
DEFAULT_MODEL = "whisper-1"


def write_log(case_id, message):
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / "transcribe_log.txt"
    now = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now}] [{case_id}] {message}\n")


def get_case_dir(case_id):
    case_dir = CASES_DIR / case_id
    if not case_dir.exists():
        raise FileNotFoundError(f"사건 폴더를 찾을 수 없습니다: {case_dir}")
    return case_dir


def find_audio_files(case_dir):
    audio_dir = case_dir / "01_audio"
    if not audio_dir.exists():
        raise FileNotFoundError(f"01_audio 폴더를 찾을 수 없습니다: {audio_dir}")

    files = [
        p for p in audio_dir.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    ]

    return sorted(files, key=lambda p: p.stat().st_mtime)


def save_transcript(case_dir, text, audio_path, model):
    transcript_dir = case_dir / "02_transcript"
    transcript_dir.mkdir(exist_ok=True)

    transcript_path = transcript_dir / "transcript.txt"
    meta_path = transcript_dir / "transcript_meta.json"

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")

    meta = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_audio": str(audio_path),
        "model": model,
        "output_file": str(transcript_path),
        "status": "TRANSCRIBED",
        "text_length": len(text.strip())
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return transcript_path, meta_path


def update_case_meta(case_dir):
    meta_path = case_dir / "case_meta.json"

    if not meta_path.exists():
        return

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        meta["status"] = "02_TRANSCRIBED"
        meta["transcribed_at"] = datetime.now().isoformat(timespec="seconds")
        meta["next_action"] = "extract_tax_facts.py로 양도세 사실관계 추출 진행"

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_log(case_dir.name, f"case_meta update failed: {e}")


def transcribe_audio(audio_path, model):
    client = OpenAI()

    with open(audio_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language="ko",
            response_format="text",
        )

    if isinstance(result, str):
        return result

    # 일부 응답 형식에서 text 속성이 있을 경우 대비
    return getattr(result, "text", str(result))


def main():
    parser = argparse.ArgumentParser(description="TaxCaseManager 음성 전사기")
    parser.add_argument("case_id", help="사건번호 예: GT-20260508-001")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="전사 모델명")
    args = parser.parse_args()

    case_id = args.case_id
    model = args.model

    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise EnvironmentError("OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")

        case_dir = get_case_dir(case_id)
        audio_files = find_audio_files(case_dir)

        if not audio_files:
            print("[STOP] 01_audio 폴더에 전사할 음성파일이 없습니다.")
            print(f"[CASE_ID] {case_id}")
            write_log(case_id, "no audio files")
            return

        audio_path = audio_files[0]

        transcript_path = case_dir / "02_transcript" / "transcript.txt"

        permission = require_ai_permission(
            task_name="transcription",
            case_id=case_id,
            output_path=transcript_path
        )

        if not permission["allowed"]:
            print("[SKIP] AI 전사 호출 생략")
            print(f"[REASON] {permission['reason']}")
            return

        print("[START] 음성 전사 시작")
        print(f"[CASE_ID] {case_id}")
        print(f"[AUDIO] {audio_path}")
        print(f"[MODEL] {model}")

        try:
            text = transcribe_audio(audio_path, model)
            
            log_ai_call(
                case_id=case_id,
                task_name="transcription",
                model=model,
                input_ref=str(audio_path),
                output_ref=str(transcript_path),
                status="SUCCESS",
                meta={
                    "text_length": len(text.strip())
                }
            )

            transcript_path, meta_path = save_transcript(case_dir, text, audio_path, model)
            update_case_meta(case_dir)

            write_log(case_id, f"transcribed audio={audio_path.name} output={transcript_path}")

            print("[SUCCESS] 음성 전사 완료")
            print(f"[TRANSCRIPT] {transcript_path}")
            print(f"[META] {meta_path}")
            print("")
            print("[NEXT]")
            print(f"python C:\\TaxCaseManager\\extract_tax_facts.py {case_id}")

        except Exception as e:
            log_ai_call(
                case_id=case_id,
                task_name="transcription",
                model=model,
                input_ref=str(audio_path),
                output_ref="",
                status="FAIL",
                meta={
                    "error": str(e)
                }
            )
            raise e

    except Exception as e:
        write_log(case_id, f"ERROR {type(e).__name__}: {e}")
        print("[FAIL] 음성 전사 실패")
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
