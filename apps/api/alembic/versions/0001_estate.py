"""Estate, source, simulated target and answer key schemas.

The answer key has its own schema so that only the scorer reads it. It must never
reach agent inputs or the UI.
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

UPGRADE = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA studio;
CREATE SCHEMA cr_source;
CREATE SCHEMA erpx_sim;
CREATE SCHEMA answer_key;

CREATE TABLE studio.customer (
    customer_id text PRIMARY KEY,
    name text NOT NULL,
    sector text NOT NULL,
    staff_count integer NOT NULL,
    erp_since integer NOT NULL,
    cr_since integer NOT NULL,
    modules_in_scope text NOT NULL,
    out_of_scope text NOT NULL,
    goal text NOT NULL,
    synthetic boolean NOT NULL
);

CREATE TABLE studio.legal_entity (
    entity_code text PRIMARY KEY,
    customer_id text NOT NULL REFERENCES studio.customer,
    name text NOT NULL,
    country text NOT NULL,
    base_currency text NOT NULL,
    status text NOT NULL,
    dormant_since date,
    in_migration_scope boolean NOT NULL
);

CREATE TABLE studio.migration_case (
    case_id text PRIMARY KEY,
    customer_id text NOT NULL REFERENCES studio.customer,
    label text NOT NULL,
    entity_code text NOT NULL REFERENCES studio.legal_entity,
    status text NOT NULL,
    window_start date NOT NULL,
    window_end date NOT NULL
);

CREATE TABLE studio.estate_item (
    item_id text PRIMARY KEY,
    case_id text NOT NULL REFERENCES studio.migration_case,
    item_type text NOT NULL,
    name text NOT NULL,
    subtype text NOT NULL,
    module text,
    owner text,
    documented boolean NOT NULL,
    j2x_explained boolean NOT NULL,
    frequency text,
    usage_12m integer NOT NULL,
    last_used date,
    direct_db_write boolean NOT NULL,
    definition jsonb NOT NULL,
    source_text text
);
CREATE INDEX ON studio.estate_item (item_type);

CREATE TABLE studio.usage_event (
    item_id text NOT NULL REFERENCES studio.estate_item,
    event_date date NOT NULL,
    event_count integer NOT NULL,
    entity_code text NOT NULL REFERENCES studio.legal_entity
);
CREATE INDEX ON studio.usage_event (item_id);

CREATE TABLE studio.j2x_explanation (
    item_id text PRIMARY KEY REFERENCES studio.estate_item,
    complexity text NOT NULL,
    summary text NOT NULL
);

CREATE TABLE studio.mapping_precedent (
    precedent_id text PRIMARY KEY,
    pattern text NOT NULL,
    source_customer text NOT NULL,
    outcome text NOT NULL,
    review_status text NOT NULL,
    synthetic boolean NOT NULL
);

CREATE TABLE cr_source.account (
    account_code text PRIMARY KEY, name text NOT NULL, account_type text NOT NULL,
    vat_code text NOT NULL, active boolean NOT NULL
);
CREATE TABLE cr_source.dimension_value (
    dimension text NOT NULL, value text NOT NULL, description text NOT NULL, active boolean NOT NULL,
    PRIMARY KEY (dimension, value)
);
CREATE TABLE cr_source.customer (
    customer_id text PRIMARY KEY, name text NOT NULL, country text NOT NULL, active boolean NOT NULL
);
CREATE TABLE cr_source.supplier (
    supplier_id text PRIMARY KEY, name text NOT NULL, country text NOT NULL, active boolean NOT NULL
);
CREATE TABLE cr_source.resource_reference (
    partner_code text PRIMARY KEY, display_name text NOT NULL, grade text NOT NULL,
    is_partner boolean NOT NULL, active boolean NOT NULL, joined_year integer NOT NULL
);
CREATE TABLE cr_source.utilisation_summary (
    period text NOT NULL, grade text NOT NULL, available_hours integer NOT NULL,
    billable_hours integer NOT NULL, PRIMARY KEY (period, grade)
);
CREATE TABLE cr_source.project (
    project_id text PRIMARY KEY, name text NOT NULL, customer_id text NOT NULL, partner_code text NOT NULL,
    service_line text NOT NULL, status text NOT NULL, start_date date NOT NULL, closed_date date
);
CREATE TABLE cr_source.fx_rate (
    currency text PRIMARY KEY, rate_date date NOT NULL, rate_text text NOT NULL
);
CREATE TABLE cr_source.ar_open_item (
    item_id text PRIMARY KEY, customer_id text NOT NULL, invoice_date date NOT NULL, due_date date NOT NULL,
    currency text NOT NULL, amount_cur_minor bigint NOT NULL, base_minor bigint NOT NULL
);
CREATE TABLE cr_source.ap_open_item (
    item_id text PRIMARY KEY, supplier_id text NOT NULL, invoice_date date NOT NULL, due_date date NOT NULL,
    currency text NOT NULL, amount_cur_minor bigint NOT NULL, base_minor bigint NOT NULL
);
CREATE TABLE cr_source.wip_item (
    wip_id text PRIMARY KEY, project_id text NOT NULL, txn_date date NOT NULL, hours_x100 bigint NOT NULL,
    cost_minor bigint NOT NULL, billable_minor bigint NOT NULL
);
CREATE TABLE cr_source.gl_balance (
    account_code text NOT NULL, period text NOT NULL, cost_centre text NOT NULL, service_line text NOT NULL,
    amount_minor bigint NOT NULL, PRIMARY KEY (account_code, period, cost_centre, service_line)
);
CREATE TABLE cr_source.account_map (
    account_code text PRIMARY KEY, erpx_account text NOT NULL
);
CREATE TABLE cr_source.dimension_map (
    dimension text NOT NULL, value text NOT NULL, erpx_value text NOT NULL,
    PRIMARY KEY (dimension, value)
);

CREATE TABLE erpx_sim.account (
    erpx_account text PRIMARY KEY, name text NOT NULL, account_type text NOT NULL, vat_code text NOT NULL
);
CREATE TABLE erpx_sim.dimension_value (
    dimension text NOT NULL, erpx_value text NOT NULL, PRIMARY KEY (dimension, erpx_value)
);
CREATE TABLE erpx_sim.customer (LIKE cr_source.customer INCLUDING ALL);
CREATE TABLE erpx_sim.supplier (LIKE cr_source.supplier INCLUDING ALL);
CREATE TABLE erpx_sim.project (LIKE cr_source.project INCLUDING ALL);
CREATE TABLE erpx_sim.fx_rate (LIKE cr_source.fx_rate INCLUDING ALL);
CREATE TABLE erpx_sim.ar_open_item (LIKE cr_source.ar_open_item INCLUDING ALL);
CREATE TABLE erpx_sim.ap_open_item (LIKE cr_source.ap_open_item INCLUDING ALL);
CREATE TABLE erpx_sim.wip_item (LIKE cr_source.wip_item INCLUDING ALL);
CREATE TABLE erpx_sim.gl_balance (
    erpx_account text NOT NULL, period text NOT NULL, cost_centre text NOT NULL, service_line text NOT NULL,
    amount_minor bigint NOT NULL, PRIMARY KEY (erpx_account, period, cost_centre, service_line)
);

CREATE TABLE answer_key.expected_decision (
    item_id text PRIMARY KEY, expected_outcome text, expected_action text, expected_state text NOT NULL,
    requires_customer boolean NOT NULL, merge_group text, planted_issue text, note text
);
CREATE TABLE answer_key.planted_issue (
    issue_id text PRIMARY KEY, issue_type text NOT NULL, planted text NOT NULL,
    expected_behaviour text NOT NULL, item_ref text, check_ref text, scene integer NOT NULL
);
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute("""
        DROP SCHEMA answer_key CASCADE;
        DROP SCHEMA erpx_sim CASCADE;
        DROP SCHEMA cr_source CASCADE;
        DROP SCHEMA studio CASCADE;
    """)
