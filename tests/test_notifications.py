"""Отправка уведомлений: Telegram, email, WhatsApp-заглушка.

Notification senders: Telegram, email, WhatsApp stub. Сеть и SMTP замоканы.
"""

from app import config, notifications

# --- Telegram ---


def test_telegram_skipped_without_token(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "")
    assert notifications.send_telegram("123", "hi") is False


def test_telegram_skipped_without_chat_id(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "tok")
    assert notifications.send_telegram("", "hi") is False


def test_telegram_success(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "secret-token")
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            return None

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return FakeResp()

    monkeypatch.setattr(notifications.httpx, "post", fake_post)
    assert notifications.send_telegram("999", "hello") is True
    assert "secret-token" in captured["url"]
    assert captured["json"]["chat_id"] == "999"
    assert captured["json"]["text"] == "hello"


def test_telegram_failure_is_caught(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "tok")

    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(notifications.httpx, "post", boom)
    assert notifications.send_telegram("999", "hello") is False


# --- Email ---


def test_email_skipped_without_host(monkeypatch):
    monkeypatch.setattr(config, "SMTP_HOST", "")
    assert notifications.send_email("a@b.c", "subj", "body") is False


def test_email_skipped_without_recipient(monkeypatch):
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.test")
    assert notifications.send_email("", "subj", "body") is False


class _FakeSMTP:
    last = None

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.tls = False
        self.logged_in = False
        self.sent = False
        _FakeSMTP.last = self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.tls = True

    def login(self, user, password):
        self.logged_in = True

    def send_message(self, msg):
        self.sent = True


def test_email_success_with_tls_and_login(monkeypatch):
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(config, "SMTP_USE_TLS", True)
    monkeypatch.setattr(config, "SMTP_USER", "user")
    monkeypatch.setattr(config, "SMTP_PASSWORD", "pw")
    monkeypatch.setattr(notifications.smtplib, "SMTP", _FakeSMTP)

    assert notifications.send_email("a@b.c", "subj", "body") is True
    sent = _FakeSMTP.last
    assert sent.tls and sent.logged_in and sent.sent


def test_email_failure_is_caught(monkeypatch):
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.test")

    def boom(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(notifications.smtplib, "SMTP", boom)
    assert notifications.send_email("a@b.c", "subj", "body") is False


# --- WhatsApp (заглушка) ---


def test_whatsapp_stub_returns_false():
    assert notifications.send_whatsapp("+10000000000", "hi") is False
