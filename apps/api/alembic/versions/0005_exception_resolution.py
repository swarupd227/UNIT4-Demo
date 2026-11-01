"""Approvals of exceptions, which outlive a run because a rerun lists the same exception again."""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE studio.exception_resolution (
            code text NOT NULL,
            title text NOT NULL,
            approved_by text NOT NULL,
            approved_role text NOT NULL,
            approved_at timestamptz NOT NULL,
            PRIMARY KEY (code, title)
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE studio.exception_resolution;")
