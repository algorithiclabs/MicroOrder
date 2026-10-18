from contextlib import contextmanager
import os
import secrets

import psycopg
from psycopg.rows import dict_row


@contextmanager
def connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required. Put the Supabase Postgres connection string in .env.")
    conn = psycopg.connect(database_url, row_factory=dict_row, prepare_threshold=None)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_connection():
    with connection() as conn:
        conn.execute("SELECT 1").fetchone()


def create_order(fields):
    order_id = secrets.token_urlsafe(9)
    owner_token = secrets.token_urlsafe(24)
    with connection() as conn:
        order = conn.execute(
            """
            INSERT INTO change_orders (
                id, owner_token, contractor_name, contractor_email, client_name,
                title, description, timeline_impact, amount_cents, currency, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            RETURNING *
            """,
            (order_id, owner_token, fields["contractor_name"], fields["contractor_email"], fields["client_name"], fields["title"], fields["description"], fields["timeline_impact"], fields["amount_cents"], fields["currency"]),
        ).fetchone()
        conn.execute("INSERT INTO events (change_order_id, event_type, occurred_at) VALUES (%s, %s, now())", (order_id, "created"))
    return order


def get_order(order_id):
    with connection() as conn:
        return conn.execute("SELECT * FROM change_orders WHERE id = %s", (order_id,)).fetchone()


def get_by_owner_token(token):
    with connection() as conn:
        return conn.execute("SELECT * FROM change_orders WHERE owner_token = %s", (token,)).fetchone()


def decide_order(order_id, decision, approver_name, approver_email):
    with connection() as conn:
        order = conn.execute(
            """
            UPDATE change_orders
            SET status = %s, decided_at = now(), approver_name = %s, approver_email = %s
            WHERE id = %s AND status = 'pending'
            RETURNING *
            """,
            (decision, approver_name, approver_email, order_id),
        ).fetchone()
        if order:
            conn.execute("INSERT INTO events (change_order_id, event_type, occurred_at) VALUES (%s, %s, now())", (order_id, decision))
        return order


def record_event(order_id, event_type):
    with connection() as conn:
        conn.execute("INSERT INTO events (change_order_id, event_type, occurred_at) VALUES (%s, %s, now())", (order_id, event_type))


def invoice_line(order):
    amount = order["amount_cents"] / 100
    return f"{order['title']} — {order['description']} — {order['currency']} {amount:,.2f}. Timeline impact: {order['timeline_impact']}"
