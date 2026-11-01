"""Token counts for artefacts a live model produced, so the cost of a run can be reported."""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE studio.artefact
            ADD COLUMN input_tokens integer,
            ADD COLUMN output_tokens integer;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE studio.artefact DROP COLUMN input_tokens, DROP COLUMN output_tokens;")
