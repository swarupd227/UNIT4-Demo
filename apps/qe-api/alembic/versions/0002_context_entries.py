"""Context entries: risk cards, hidden rules and dead code, each reviewed by a named engineer.

Only approved entries are exported to the Context Engine.
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE qe.context_entry (
    entry_id text PRIMARY KEY,
    kind text NOT NULL CHECK (kind IN ('risk_card', 'hidden_rule', 'dead_code')),
    rule text,
    title text NOT NULL,
    content jsonb NOT NULL,
    provenance text NOT NULL CHECK (provenance IN ('ai_analysis', 'verified_by_code')),
    source text NOT NULL,
    model text,
    input_hash text,
    status text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved', 'rejected')),
    reviewed_by text REFERENCES qe.person (person_key),
    reviewed_at timestamptz,
    review_note text,
    created_at timestamptz NOT NULL DEFAULT now()
);
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("DROP TABLE qe.context_entry")
