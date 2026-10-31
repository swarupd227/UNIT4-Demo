"""Proposals, decisions, approvals, customer questions and the audit trail.

Agents write only to agent_signal and proposal. Decisions and approvals are written only by
a named role, through the decisions API.
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

UPGRADE = """
CREATE TABLE studio.agent_signal (
    item_id text PRIMARY KEY REFERENCES studio.estate_item,
    summary text NOT NULL,
    purpose_known boolean NOT NULL,
    standard_feature text,
    standard_confidence integer,
    merge_target text,
    action_note text,
    proposal_note text,
    question text,
    conflict jsonb,
    evidence jsonb NOT NULL
);

CREATE TABLE studio.dependency (
    item_id text NOT NULL REFERENCES studio.estate_item,
    depends_on text NOT NULL REFERENCES studio.estate_item,
    table_name text NOT NULL,
    PRIMARY KEY (item_id, depends_on, table_name)
);

CREATE TABLE studio.proposal (
    item_id text PRIMARY KEY REFERENCES studio.estate_item,
    outcome text,
    candidate_outcome text,
    action text,
    state text NOT NULL,
    reason text NOT NULL,
    confidence integer,
    rule text NOT NULL,
    flags jsonb NOT NULL,
    evidence jsonb NOT NULL,
    engine_version text NOT NULL
);

CREATE TABLE studio.decision (
    item_id text PRIMARY KEY REFERENCES studio.proposal,
    outcome text,
    action text,
    status text NOT NULL,
    conflict_open boolean NOT NULL,
    edit_reason text,
    updated_at timestamptz NOT NULL
);
CREATE INDEX ON studio.decision (status);

CREATE TABLE studio.approval (
    item_id text NOT NULL REFERENCES studio.decision,
    role text NOT NULL,
    person text NOT NULL,
    decided_at timestamptz NOT NULL,
    PRIMARY KEY (item_id, role)
);

CREATE TABLE studio.customer_question (
    question_id bigserial PRIMARY KEY,
    item_id text NOT NULL REFERENCES studio.decision,
    question text NOT NULL,
    options jsonb NOT NULL,
    status text NOT NULL,
    asked_by text NOT NULL,
    asked_at timestamptz NOT NULL,
    answer text,
    answered_by text,
    answered_at timestamptz
);
CREATE INDEX ON studio.customer_question (item_id);
CREATE UNIQUE INDEX one_open_question ON studio.customer_question (item_id) WHERE status = 'open';

CREATE TABLE studio.audit_event (
    seq bigserial PRIMARY KEY,
    at timestamptz NOT NULL,
    actor text NOT NULL,
    role text NOT NULL,
    action text NOT NULL,
    item_id text NOT NULL,
    detail jsonb NOT NULL,
    prev_hash text NOT NULL,
    hash text NOT NULL
);
CREATE INDEX ON studio.audit_event (item_id);

CREATE FUNCTION studio.reject_audit_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_event is append-only';
END;
$$;
CREATE TRIGGER audit_event_append_only BEFORE UPDATE OR DELETE ON studio.audit_event
    FOR EACH ROW EXECUTE FUNCTION studio.reject_audit_change();
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("""
        DROP TABLE studio.audit_event, studio.customer_question, studio.approval, studio.decision,
                   studio.proposal, studio.dependency, studio.agent_signal;
        DROP FUNCTION studio.reject_audit_change();
    """)
