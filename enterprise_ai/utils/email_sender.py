"""
utils/email_sender.py
Sends invitation emails to new users added by admin.

Uses Python stdlib smtplib — no external dependencies.

Configure in .env:
    EMAIL_HOST      = smtp.gmail.com
    EMAIL_PORT      = 587
    EMAIL_USER      = yourapp@gmail.com
    EMAIL_PASSWORD  = your_gmail_app_password   ← NOT your normal password
    EMAIL_FROM_NAME = Nova AI

Gmail setup:
    1. Go to myaccount.google.com → Security → 2-Step Verification (enable)
    2. Then → App Passwords → create one for "Nova AI"
    3. Use that 16-char app password as EMAIL_PASSWORD
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _smtp_config() -> dict:
    return {
        "host":      os.getenv("EMAIL_HOST",      "smtp.gmail.com"),
        "port":      int(os.getenv("EMAIL_PORT",  "587")),
        "user":      os.getenv("EMAIL_USER",      ""),
        "password":  os.getenv("EMAIL_PASSWORD",  ""),
        "from_name": os.getenv("EMAIL_FROM_NAME", "Nova AI"),
    }


def send_invite_email(
    to_email:     str,
    company_name: str,
    join_code:    str,
    role:         str,
    invited_by:   str = "your admin",
) -> bool:
    """
    Send a workspace invitation email to a new user.
    Returns True on success, False if email is not configured or fails.
    """
    cfg = _smtp_config()

    if not cfg["user"] or not cfg["password"]:
        logger.warning(
            "[EmailSender] EMAIL_USER or EMAIL_PASSWORD not set — "
            "skipping invite email. Set them in .env to enable."
        )
        return False

    role_label = {
        "employee":  "Employee",
        "team_lead": "Team Lead",
        "manager":   "Manager",
        "admin":     "Admin",
    }.get(role, role.capitalize())

    subject = f"You've been invited to {company_name} on Nova AI"

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
  <div style="max-width: 560px; margin: auto; background: white;
              border-radius: 12px; padding: 40px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">

    <h2 style="color: #1a1a2e; margin-bottom: 4px;">Welcome to {company_name} 👋</h2>
    <p style="color: #555; margin-top: 0;">
      {invited_by} has invited you to join <strong>{company_name}</strong>
      on <strong>Nova AI</strong> as <strong>{role_label}</strong>.
    </p>

    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

    <p style="color: #333; font-size: 15px; margin-bottom: 8px;">
      Your company join code:
    </p>
    <div style="background: #1a1a2e; color: #fff; font-size: 28px;
                font-weight: bold; letter-spacing: 6px; text-align: center;
                padding: 18px; border-radius: 8px; margin-bottom: 24px;">
      {join_code}
    </div>

    <h3 style="color: #1a1a2e;">How to get started:</h3>
    <ol style="color: #555; line-height: 1.9;">
      <li>Go to the Nova AI login page</li>
      <li>Click <strong>"Register"</strong></li>
      <li>Enter the join code above, your email (<strong>{to_email}</strong>), and choose a password</li>
      <li>Done — log in and start using your company AI assistant!</li>
    </ol>

    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

    <p style="color: #999; font-size: 12px; text-align: center;">
      This invitation was sent by {invited_by} from {company_name}.<br>
      If you weren't expecting this, you can safely ignore this email.<br><br>
      <strong>Nova AI — Enterprise AI Assistant</strong>
    </p>
  </div>
</body>
</html>
"""

    plain_body = (
        f"You've been invited to {company_name} on Nova AI as {role_label}.\n\n"
        f"Your company join code: {join_code}\n\n"
        f"Steps:\n"
        f"1. Go to the Nova AI login page\n"
        f"2. Click Register\n"
        f"3. Enter join code: {join_code}\n"
        f"4. Enter your email: {to_email}\n"
        f"5. Choose a password and you're in!\n\n"
        f"Invited by: {invited_by}"
    )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{cfg['from_name']} <{cfg['user']}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body,  "html"))

        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(cfg["user"], cfg["password"])
            smtp.sendmail(cfg["user"], to_email, msg.as_string())

        logger.info(
            f"[EmailSender] Invite sent → {to_email} | "
            f"company={company_name} | role={role}"
        )
        return True

    except Exception as e:
        logger.error(f"[EmailSender] Failed to send invite to {to_email}: {e}")
        return False
