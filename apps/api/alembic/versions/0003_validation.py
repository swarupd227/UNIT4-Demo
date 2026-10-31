"""Reference documents, agent artefacts, reconciliation runs, exceptions and mapping memory."""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE studio.reference_document (
    document_key text PRIMARY KEY,
    content jsonb NOT NULL
);

CREATE TABLE erpx_sim.utilisation_summary (LIKE cr_source.utilisation_summary INCLUDING ALL);

CREATE TABLE studio.artefact (
    item_id text NOT NULL REFERENCES studio.estate_item,
    kind text NOT NULL,
    content jsonb NOT NULL,
    source text NOT NULL,
    model text,
    duration_ms integer,
    prompt_version text NOT NULL,
    input_hash text NOT NULL,
    PRIMARY KEY (item_id, kind)
);

CREATE TABLE studio.check_run (
    run_id bigserial PRIMARY KEY,
    started_at timestamptz NOT NULL,
    finished_at timestamptz NOT NULL,
    definitions_hash text NOT NULL,
    input_hash text NOT NULL,
    result_hash text NOT NULL
);

CREATE TABLE studio.check_result (
    run_id bigint NOT NULL REFERENCES studio.check_run ON DELETE CASCADE,
    check_id text NOT NULL,
    version integer NOT NULL,
    name text NOT NULL,
    compares text NOT NULL,
    tolerance text NOT NULL,
    status text NOT NULL,
    unit text NOT NULL,
    source_value bigint,
    target_value bigint,
    source_count bigint,
    target_count bigint,
    difference_count integer NOT NULL,
    summary jsonb NOT NULL,
    PRIMARY KEY (run_id, check_id)
);

CREATE TABLE studio.check_difference (
    run_id bigint NOT NULL REFERENCES studio.check_run ON DELETE CASCADE,
    check_id text NOT NULL,
    row_number integer NOT NULL,
    row_key text NOT NULL,
    source_value bigint,
    target_value bigint,
    difference bigint,
    detail jsonb NOT NULL,
    PRIMARY KEY (run_id, check_id, row_number)
);

CREATE TABLE studio.exception (
    run_id bigint NOT NULL REFERENCES studio.check_run ON DELETE CASCADE,
    exception_id text NOT NULL,
    check_id text NOT NULL,
    code text NOT NULL,
    title text NOT NULL,
    cause text NOT NULL,
    proposed_action text NOT NULL,
    approver_role text NOT NULL,
    amount_minor bigint,
    detail jsonb NOT NULL,
    status text NOT NULL,
    PRIMARY KEY (run_id, exception_id)
);

CREATE TABLE studio.mapping_memory (
    memory_id bigserial PRIMARY KEY,
    item_id text NOT NULL,
    pattern text NOT NULL,
    outcome text NOT NULL,
    review_status text NOT NULL,
    decided_by text NOT NULL,
    decided_at timestamptz NOT NULL,
    reason text
);
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("""
        DROP TABLE studio.mapping_memory, studio.exception, studio.check_difference, studio.check_result,
                   studio.check_run, studio.artefact, erpx_sim.utilisation_summary,
                   studio.reference_document;
    """)
