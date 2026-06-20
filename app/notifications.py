"""Отправка уведомлений: Telegram + email. / Notification senders: Telegram + email.

WhatsApp намеренно вынесен отдельно: его подключают позже через WhatsApp
Business API (Twilio / 360dialog) — см. ``send_whatsapp`` ниже как заглушку.

WhatsApp is intentionally a separate stub: wire it later via the WhatsApp
Business API (Twilio / 360dialog) — see ``send_whatsapp`` below.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import httpx

from . import config

log = logging.getLogger("notifications")


def send_telegram(chat_id: str, text: str) -> bool:
    if not config.TELEGRAM_BOT_TOKEN or not chat_id:
        log.info("Telegram skipped (no token or chat_id)")
        return False
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = httpx.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Telegram send failed: %s", exc)
        return False


def send_email(to_addr: str, subject: str, body: str) -> bool:
    if not config.SMTP_HOST or not to_addr:
        log.info("Email skipped (no SMTP host or recipient)")
        return False
    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as smtp:
            if config.SMTP_USE_TLS:
                smtp.starttls()
            if config.SMTP_USER:
                smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Email send failed: %s", exc)
        return False


def send_whatsapp(phone: str, text: str) -> bool:
    """Заглушка для будущего WhatsApp Business API. / Stub for future WhatsApp."""
    log.info("WhatsApp not configured yet (phone=%s)", phone)
    return False
