from decimal import Decimal, InvalidOperation
from email.utils import parseaddr
import os
import re

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

import db
import mailer

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "local-dev-only")


@app.after_request
def security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def valid_email(value):
    address = parseaddr(value or "")[1]
    return bool(address and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", address))


def amount_to_cents(value):
    try:
        amount = Decimal(value).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        raise ValueError("Amount must be a valid number.")
    cents = int(amount * 100)
    if cents <= 0 or cents > 100_000_000:
        raise ValueError("Amount must be between 0.01 and 1,000,000.00.")
    return cents


def form_value(name):
    return request.form.get(name, "").strip()


@app.get("/")
def create_page():
    return render_template("create.html", values={})


@app.post("/change-orders")
def create_change_order():
    fields = {
        "contractor_name": form_value("contractor_name"),
        "contractor_email": form_value("contractor_email"),
        "client_name": form_value("client_name"),
        "title": form_value("title"),
        "description": form_value("description"),
        "timeline_impact": form_value("timeline_impact") or "No impact specified",
        "currency": form_value("currency") or "USD",
    }
    if not all(fields[name] for name in ("contractor_name", "client_name", "title", "description")):
        flash("Complete all required fields.", "error")
        return render_template("create.html", values=fields), 400
    if not valid_email(fields["contractor_email"]):
        flash("Enter a valid contractor email.", "error")
        return render_template("create.html", values=fields), 400
    try:
        fields["amount_cents"] = amount_to_cents(form_value("amount"))
    except ValueError as exc:
        flash(str(exc), "error")
        return render_template("create.html", values=fields), 400

    order = db.create_order(fields)
    public_url = url_for("public_order", order_id=order["id"], _external=True)
    owner_url = url_for("manage_order", token=order["owner_token"], _external=True)
    sent = mailer.send_created(order, public_url, owner_url)
    db.record_event(order["id"], "creation_notification_sent" if sent else "creation_notification_failed")
    return render_template(
        "created.html",
        order=order,
        public_url=public_url,
        owner_url=owner_url,
        notification_sent=sent,
    )


@app.get("/o/<order_id>")
def public_order(order_id):
    order = db.get_order(order_id)
    if not order:
        abort(404)
    return render_template("public_order.html", order=order)


@app.post("/o/<order_id>/decide")
def decide_order(order_id):
    decision = form_value("decision")
    approver_name = form_value("approver_name")
    approver_email = form_value("approver_email")
    if decision not in {"approved", "declined"} or not approver_name or not valid_email(approver_email):
        flash("Name and valid email are required.", "error")
        return redirect(url_for("public_order", order_id=order_id))

    changed_order = db.decide_order(order_id, decision, approver_name, approver_email)
    order = changed_order or db.get_order(order_id)
    if not order:
        abort(404)

    if changed_order:
        sent = mailer.send_decision(order)
        db.record_event(order_id, "notification_sent" if sent else "notification_failed")
        if sent:
            flash(f"Change order {decision}. Confirmation email sent.", "success")
        else:
            flash(f"Change order {decision}. Email notification failed; the decision is still saved.", "warning")
    return redirect(url_for("public_order", order_id=order_id))


@app.get("/manage/<token>")
def manage_order(token):
    order = db.get_by_owner_token(token)
    if not order:
        abort(404)
    return render_template(
        "manage_order.html",
        order=order,
        invoice_line=db.invoice_line(order),
        public_url=url_for("public_order", order_id=order["id"], _external=True),
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("message.html", title="Not found", message="This link does not exist or is no longer available."), 404


def main():
    db.check_connection()
    app.run(host=os.environ.get("MICROORDER_HOST", "127.0.0.1"), port=int(os.environ.get("MICROORDER_PORT", "8000")), debug=False)


if __name__ == "__main__":
    main()
