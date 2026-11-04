"""Puts the workbench back to the start of the story, for a rehearsal or a fresh run.

    python -m app.reset          (npm run qe:reset)

Rebuilds the module's repository from its history, so the pull request is open again, and clears
every review, merge and audit event. Agent recordings and lab results are kept: they are the evidence.
"""

import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from app.context import analysis, sync_entries
from app.db import get_engine

HISTORY = Path(__file__).resolve().parents[3] / "qe" / "history" / "build_history.py"


def main() -> None:
    subprocess.run([sys.executable, str(HISTORY)], check=True, stdout=subprocess.DEVNULL)
    with get_engine().begin() as db:
        db.execute(text("TRUNCATE qe.pr_review, qe.pr_merge, qe.change_review, qe.audit_event"))
        db.execute(
            text("""
                UPDATE qe.context_entry
                SET status = 'proposed', reviewed_by = NULL, reviewed_at = NULL, review_note = NULL
            """)
        )
        sync_entries(db, analysis())
    print("The workbench is back at the start: nothing reviewed, nothing merged.")


if __name__ == "__main__":
    main()
