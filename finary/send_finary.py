#!/usr/bin/env python3
"""Render THE FINARY HTML to a PDF and email it — built for unattended daily runs.

The daily automation must complete with no human in the loop, so this script
avoids interactive OAuth entirely and sends through whichever mail credential is
present in the environment (injected as secrets). Providers are auto-detected in
priority order; override with --provider.

  Provider      Required environment variables
  ------------  ------------------------------------------------------------
  resend        RESEND_API_KEY              (from: RESEND_FROM or onboarding@resend.dev)
  sendgrid      SENDGRID_API_KEY, SENDGRID_FROM
  gmail         GMAIL_ADDRESS, GMAIL_APP_PASSWORD
  smtp          SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM

Examples
--------
  # Render HTML -> PDF and send
  python finary/send_finary.py --html issue.html --to a@b.com \
      --subject "THE FINARY — 2026-09-23"

  # Send an already-rendered PDF
  python finary/send_finary.py --pdf issue.pdf --to a@b.com \
      --subject "THE FINARY — 2026-09-23"

  # Prove the pipeline without sending (no credentials needed)
  python finary/send_finary.py --html issue.html --to a@b.com \
      --subject "test" --dry-run

Exit code is non-zero on any failure so the automation can detect a bad run.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import smtplib
import sys
import tempfile
import urllib.error
import urllib.request
from email.message import EmailMessage

PROVIDERS = ("resend", "sendgrid", "gmail", "smtp")


def log(msg: str) -> None:
    print(f"[finary] {msg}", flush=True)


def detect_provider() -> str | None:
    """Pick the first provider whose required secrets are all present."""
    if os.environ.get("RESEND_API_KEY"):
        return "resend"
    if os.environ.get("SENDGRID_API_KEY") and os.environ.get("SENDGRID_FROM"):
        return "sendgrid"
    if os.environ.get("GMAIL_ADDRESS") and os.environ.get("GMAIL_APP_PASSWORD"):
        return "gmail"
    if all(os.environ.get(k) for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")):
        return "smtp"
    return None


def render_pdf(html_path: str, pdf_path: str) -> str:
    """Render an HTML file to PDF with WeasyPrint."""
    try:
        from weasyprint import HTML  # imported lazily so --pdf sends need no toolchain
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "WeasyPrint is not installed. Run: pip install -r finary/requirements.txt"
        ) from exc
    log(f"rendering {html_path} -> {pdf_path}")
    HTML(filename=html_path).write_pdf(pdf_path)
    size = os.path.getsize(pdf_path)
    log(f"rendered PDF ({size // 1024} KB)")
    return pdf_path


# --------------------------------------------------------------------------- #
# Providers
# --------------------------------------------------------------------------- #
def send_smtp(host, port, username, password, sender, to, subject, body, pdf_path, use_starttls=True):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with open(pdf_path, "rb") as fh:
        msg.add_attachment(
            fh.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(pdf_path),
        )
    log(f"connecting to SMTP {host}:{port} as {username}")
    with smtplib.SMTP(host, int(port), timeout=60) as server:
        server.ehlo()
        if use_starttls:
            server.starttls()
            server.ehlo()
        server.login(username, password)
        server.send_message(msg)
    log(f"sent via SMTP to {to}")


def send_gmail(to, subject, body, pdf_path):
    addr = os.environ["GMAIL_ADDRESS"]
    send_smtp(
        host="smtp.gmail.com",
        port=587,
        username=addr,
        password=os.environ["GMAIL_APP_PASSWORD"],
        sender=os.environ.get("GMAIL_FROM", f"THE FINARY <{addr}>"),
        to=to,
        subject=subject,
        body=body,
        pdf_path=pdf_path,
    )


def send_generic_smtp(to, subject, body, pdf_path):
    send_smtp(
        host=os.environ["SMTP_HOST"],
        port=os.environ["SMTP_PORT"],
        username=os.environ["SMTP_USERNAME"],
        password=os.environ["SMTP_PASSWORD"],
        sender=os.environ["SMTP_FROM"],
        to=to,
        subject=subject,
        body=body,
        pdf_path=pdf_path,
        use_starttls=os.environ.get("SMTP_STARTTLS", "true").lower() != "false",
    )


def _post_json(url, headers, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def send_resend(to, subject, body, pdf_path):
    sender = os.environ.get("RESEND_FROM", "THE FINARY <onboarding@resend.dev>")
    with open(pdf_path, "rb") as fh:
        content_b64 = base64.b64encode(fh.read()).decode()
    payload = {
        "from": sender,
        "to": [to],
        "subject": subject,
        "text": body,
        "attachments": [{"filename": os.path.basename(pdf_path), "content": content_b64}],
    }
    status, resp = _post_json(
        "https://api.resend.com/emails",
        {
            "Authorization": f"Bearer {os.environ['RESEND_API_KEY']}",
            "Content-Type": "application/json",
        },
        payload,
    )
    if status not in (200, 201):
        raise SystemExit(f"Resend send failed (HTTP {status}): {resp}")
    log(f"sent via Resend to {to}: {resp}")


def send_sendgrid(to, subject, body, pdf_path):
    with open(pdf_path, "rb") as fh:
        content_b64 = base64.b64encode(fh.read()).decode()
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": os.environ["SENDGRID_FROM"]},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
        "attachments": [{
            "content": content_b64,
            "filename": os.path.basename(pdf_path),
            "type": "application/pdf",
            "disposition": "attachment",
        }],
    }
    status, resp = _post_json(
        "https://api.sendgrid.com/v3/mail/send",
        {
            "Authorization": f"Bearer {os.environ['SENDGRID_API_KEY']}",
            "Content-Type": "application/json",
        },
        payload,
    )
    if status not in (200, 202):
        raise SystemExit(f"SendGrid send failed (HTTP {status}): {resp}")
    log(f"sent via SendGrid to {to} (HTTP {status})")


DISPATCH = {
    "resend": send_resend,
    "sendgrid": send_sendgrid,
    "gmail": send_gmail,
    "smtp": send_generic_smtp,
}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render and email THE FINARY.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--html", help="Path to the newspaper HTML to render into a PDF.")
    src.add_argument("--pdf", dest="pdf_in", help="Path to an already-rendered PDF to send.")
    parser.add_argument("--to", required=True, help="Recipient email address.")
    parser.add_argument("--subject", required=True, help="Email subject.")
    parser.add_argument("--body", default="Your THE FINARY commute edition is attached.",
                        help="One-line email body.")
    parser.add_argument("--out", help="Where to write the rendered PDF (default: temp file).")
    parser.add_argument("--provider", choices=PROVIDERS,
                        help="Force a provider instead of auto-detecting.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Render and report the chosen provider, but do not send.")
    args = parser.parse_args(argv)

    # 1) Obtain the PDF (render from HTML, or use the provided PDF).
    if args.html:
        out = args.out or os.path.join(tempfile.gettempdir(), "the_finary.pdf")
        pdf_path = render_pdf(args.html, out)
    else:
        pdf_path = args.pdf_in
        if not os.path.isfile(pdf_path):
            log(f"ERROR: PDF not found: {pdf_path}")
            return 2
        log(f"using existing PDF: {pdf_path} ({os.path.getsize(pdf_path) // 1024} KB)")

    # 2) Choose provider.
    provider = args.provider or detect_provider()
    if not provider:
        log("ERROR: no mail credential found. Set one provider's secrets "
            "(RESEND_API_KEY | SENDGRID_API_KEY+SENDGRID_FROM | "
            "GMAIL_ADDRESS+GMAIL_APP_PASSWORD | SMTP_*).")
        return 3
    log(f"provider: {provider}")

    if args.dry_run:
        log(f"DRY-RUN ok — would email '{args.subject}' to {args.to} via {provider} "
            f"with attachment {os.path.basename(pdf_path)}. No message sent.")
        return 0

    # 3) Send.
    try:
        DISPATCH[provider](args.to, args.subject, args.body, pdf_path)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - surface any provider error to the run
        log(f"ERROR: send failed via {provider}: {exc!r}")
        return 4
    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
