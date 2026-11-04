"""Engineer reviews of maintenance changes: flaky-test fixes and selector repairs.

A change to an existing test is applied only after a named engineer approves it.
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE qe.change_review (
    change_id text PRIMARY KEY,
    kind text NOT NULL CHECK (kind IN ('flaky_fix', 'selector_repair')),
    status text NOT NULL CHECK (status IN ('approved', 'rejected')),
    reviewed_by text NOT NULL REFERENCES qe.person (person_key),
    reviewed_at timestamptz NOT NULL,
    note text
);
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("DROP TABLE qe.change_review")
