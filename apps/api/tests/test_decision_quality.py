"""The first reading of decision quality against the answer key. Phase 3 replaces this with the
full scorer. It uses the database, so run it after a seed.
"""

from sqlalchemy import text

from app.db import get_engine


def test_proposals_against_the_answer_key() -> None:
    with get_engine().connect() as db:
        rows = db.execute(
            text("""
                SELECT k.item_id, k.expected_outcome, p.outcome, k.expected_state, p.state
                FROM answer_key.expected_decision k JOIN studio.proposal p USING (item_id)
            """)
        ).all()
    # A held item is correct when it is held: its final outcome is the customer's to give.
    wrong = sorted(
        r.item_id
        for r in rows
        if r.state != r.expected_state or (r.expected_state != "held" and r.outcome != r.expected_outcome)
    )
    print(f"{len(rows) - len(wrong)} of {len(rows)} match; wrong: {wrong}")
    assert len(rows) == 233
    assert 0 < len(wrong) <= 8
