"""Tests for the tamper-evident audit chain.

Uses an isolated temp database so the tests never touch the app's real
obscura.db (which may be locked by a running backend on Windows).
"""
import importlib
from app import store
from app.vault import audit


def _fresh(tmp_path, monkeypatch):
    db = tmp_path / "test_audit.db"
    monkeypatch.setattr(store, "DB_PATH", str(db))
    store.init_db()


def test_chain_verifies_when_intact(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    audit.append("seal", ["system"], "rec1", "captured")
    audit.append("breakglass_unlock", ["police", "judiciary"], "rec1", "warrant")
    assert audit.verify_chain() is True


def test_chain_detects_tampering(tmp_path, monkeypatch):
    import sqlite3
    _fresh(tmp_path, monkeypatch)
    audit.append("seal", ["system"], "rec1", "captured")
    audit.append("breakglass_unlock", ["police"], "rec1", "warrant")
    c = sqlite3.connect(store.DB_PATH)
    c.execute("UPDATE audit SET reason='altered' WHERE action='breakglass_unlock'")
    c.commit(); c.close()
    assert audit.verify_chain() is False
