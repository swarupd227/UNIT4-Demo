"""The audit trail and the people who act in the workbench.

Agents never write to the audit trail. Every event is made by a named person in a role.
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

UPGRADE = """
CREATE SCHEMA IF NOT EXISTS qe;

CREATE TABLE qe.person (
    person_key text PRIMARY KEY,
    name text NOT NULL,
    role text NOT NULL CHECK (role IN ('qe_lead', 'engineer', 'full_circuit_owner')),
    org text NOT NULL
);

CREATE TABLE qe.audit_event (
    seq bigserial PRIMARY KEY,
    at timestamptz NOT NULL,
    actor text NOT NULL,
    role text NOT NULL,
    action text NOT NULL,
    item_id text NOT NULL,
    detail jsonb NOT NULL,
    prev_hash text NOT NULL,
    hash text NOT NULL UNIQUE
);

INSERT INTO qe.person (person_key, name, role, org) VALUES
    ('qe_lead', 'Maria Lindgren', 'qe_lead', 'Unit4'),
    ('engineer', 'Ravi Menon', 'engineer', 'Unit4'),
    ('full_circuit_owner', 'Hanna Koskela', 'full_circuit_owner', 'Unit4');
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("DROP SCHEMA qe CASCADE")
