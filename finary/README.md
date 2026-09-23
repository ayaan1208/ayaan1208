# THE FINARY — daily email automation

`THE FINARY` is a scheduled Cursor automation (cron `0 8 * * *`) that each morning
researches the day's news, writes a newspaper-style HTML, renders it to an ~8–9
page PDF, and emails it to the reader.

For the run to be **hands-off**, the email step must not depend on interactive
OAuth (the Gmail MCP requires a human to click "authorize", which no 08:00
unattended run can do). This directory provides a credential-based sender that
uses a stored secret instead.

## `send_finary.py`

Renders HTML → PDF (WeasyPrint) and emails it via whichever mail credential is
present in the environment. It never prompts, and exits non-zero on failure so a
bad run is detectable.

```bash
# Render today's HTML and send
python finary/send_finary.py \
  --html /tmp/finary/finary.html \
  --to ayanpathan012@gmail.com \
  --subject "THE FINARY — $(date +%F)" \
  --body "Your THE FINARY commute edition is attached."

# Send an already-rendered PDF
python finary/send_finary.py --pdf out.pdf --to you@example.com --subject "..."

# Prove the pipeline without sending (no secret needed)
python finary/send_finary.py --html finary.html --to you@example.com --subject t --dry-run
```

## Choose one mail provider (add as a secret)

Providers are auto-detected in this order; set exactly one group:

| Provider | Secrets to add | Notes |
| --- | --- | --- |
| **Gmail SMTP** | `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` | Keeps your Gmail. Needs 2-Step Verification + an App Password. Recommended. |
| **Resend** | `RESEND_API_KEY` (optional `RESEND_FROM`) | Fastest API path; can send from `onboarding@resend.dev` to your own inbox. |
| **SendGrid** | `SENDGRID_API_KEY`, `SENDGRID_FROM` | `SENDGRID_FROM` must be a verified sender. |
| **Generic SMTP** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` | Any provider; STARTTLS on by default. |

Add secrets in the Secrets panel so they are injected into every future run's VM.

## Environment

The PDF toolchain is baked into the environment via `.cursor/environment.json`
(`pip install -r finary/requirements.txt`), so every fresh daily VM can render
without installing packages ad hoc.

## Recommended automation prompt change

Replace the automation's final delivery instruction ("email via Gmail") with:

> Save the newspaper HTML to `/tmp/finary/finary.html`, then deliver it by running:
> `python finary/send_finary.py --html /tmp/finary/finary.html --to ayanpathan012@gmail.com --subject "THE FINARY — <date>" --body "<one line>"`.
> Do not use interactive email tools.

This makes rendering + delivery deterministic and unattended.
