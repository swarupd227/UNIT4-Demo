"""The pull request: an engineer's decision on each test or fix in it, and the merge.

Only approved items are merged, by a real Git commit in the module's repository.
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE qe.pr_review (
    item_id text PRIMARY KEY,
    decision text NOT NULL CHECK (decision IN ('approved', 'rejected')),
    reviewed_by text NOT NULL REFERENCES qe.person (person_key),
    reviewed_at timestamptz NOT NULL,
    note text
);

CREATE TABLE qe.pr_merge (
    pr_id text PRIMARY KEY,
    merged_by text NOT NULL REFERENCES qe.person (person_key),
    merged_at timestamptz NOT NULL,
    branch text NOT NULL,
    branch_commit text NOT NULL,
    merge_commit text NOT NULL,
    items jsonb NOT NULL
);
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("DROP TABLE qe.pr_merge; DROP TABLE qe.pr_review")
