import os

import resend


def send_decision(order):
    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("RESEND_FROM")
    if not api_key or not sender:
        return False
    resend.api_key = api_key
    status = order["status"]
    html = f"""
    <p><strong>{order['client_name']}</strong> has {status} this change order:</p>
    <p><strong>{order['title']}</strong><br>{order['description']}</p>
    <p>Amount: <strong>{order['currency']} {order['amount_cents'] / 100:,.2f}</strong><br>
    Timeline impact: <strong>{order['timeline_impact']}</strong></p>
    <p>Approver: {order['approver_name']} ({order['approver_email']})</p>
    <p>This is an approval record, not a payment receipt or legal guarantee.</p>
    """
    recipients = {order["contractor_email"], order["approver_email"]}
    try:
        resend.Emails.send({
            "from": sender,
            "to": list(recipients),
            "subject": f"Change order {status}: {order['title']}",
            "html": html,
        })
        return True
    except Exception:
        return False


def send_created(order, public_url, owner_url):
    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("RESEND_FROM")
    if not api_key or not sender:
        return False
    resend.api_key = api_key
    html = f"""
    <p>Your MicroOrder change-order link is ready.</p>
    <p><strong>{order['title']}</strong> for {order['client_name']}<br>
    Amount: <strong>{order['currency']} {order['amount_cents'] / 100:,.2f}</strong><br>
    Timeline impact: <strong>{order['timeline_impact']}</strong></p>
    <p><a href="{public_url}">Client approval link</a></p>
    <p><a href="{owner_url}">Private owner link</a> — keep this link secret. It is how you recover this order in v0.1.</p>
    """
    try:
        resend.Emails.send({"from": sender, "to": [order["contractor_email"]], "subject": f"Your MicroOrder link: {order['title']}", "html": html})
        return True
    except Exception:
        return False
