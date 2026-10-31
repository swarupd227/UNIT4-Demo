"""Sign-off packs and the workbench's own timing log."""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE studio.signoff_pack (
    pack_id bigserial PRIMARY KEY,
    generated_at timestamptz NOT NULL,
    generated_by text NOT NULL,
    run_id bigint NOT NULL,
    audit_head text NOT NULL,
    manifest_hash text NOT NULL,
    summary jsonb NOT NULL,
    signed_by text,
    signed_at timestamptz
);

CREATE TABLE studio.timing_event (
    timing_id bigserial PRIMARY KEY,
    stage text NOT NULL,
    role text NOT NULL,
    seconds integer NOT NULL,
    recorded_at timestamptz NOT NULL
);
CREATE INDEX ON studio.timing_event (stage);
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("DROP TABLE studio.timing_event, studio.signoff_pack;")
