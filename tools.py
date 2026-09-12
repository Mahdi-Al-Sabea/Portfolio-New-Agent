"""
tools.py
Executable tools for Mahdi's AI Digital Twin Agent:
1. record_user_email: Records visitor contact email for follow-up.
2. record_unanswered_question: Records questions the agent does not know.
"""

import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
RECORDS_DIR = BASE_DIR / "records"
RECORDS_DIR.mkdir(exist_ok=True)

EMAILS_FILE = RECORDS_DIR / "visitor_emails.json"
UNANSWERED_FILE = RECORDS_DIR / "unanswered_questions.json"


def _append_record(file_path: Path, new_entry: dict):
    """Safely appends a JSON dictionary to an existing array file."""
    records = []
    if file_path.exists():
        try:
            records = json.loads(file_path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                records = []
        except Exception:
            records = []

    records.append(new_entry)
    file_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def record_user_email(email: str, notes: str = "") -> str:
    """
    Record a website visitor's email address and message for follow-up.

    Args:
        email: The visitor's email address (e.g. name@company.com).
        notes: Optional context, inquiry details, or what they would like to discuss.

    Returns:
        A confirmation message indicating that the email has been logged.
    """
    cleaned_email = email.strip()
    if "@" not in cleaned_email or "." not in cleaned_email:
        return f"Error: '{email}' does not appear to be a valid email address. Please ask the user to double check."

    entry = {
        "timestamp": datetime.now().isoformat(),
        "email": cleaned_email,
        "notes": notes.strip() if notes else "No additional notes provided",
    }
    _append_record(EMAILS_FILE, entry)
    print(f"[Tool] Recorded visitor email: {cleaned_email}")
    return f"Success: Recorded email '{cleaned_email}'. Inform the visitor that Mahdi has received their contact information and will be in touch shortly."


def record_unanswered_question(question: str, context: str = "") -> str:
    """
    Record a question that the AI digital twin does not know the answer to, so Mahdi can review it later.

    Args:
        question: The user's specific question that could not be answered from the CV/profile.
        context: Any brief context about what was asked.

    Returns:
        A confirmation message indicating the question was logged for Mahdi's review.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question.strip(),
        "context": context.strip(),
    }
    _append_record(UNANSWERED_FILE, entry)
    print(f"[Tool] Recorded unanswered question: {question}")
    return "Success: The question has been recorded for Mahdi to review. Tell the user honestly that you don't know the answer, that you have noted the question down for Mahdi, and offer to take their email if they'd like a direct answer."

