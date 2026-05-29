"""Tests for the tamper-evident audit chain."""
import os, sqlite3
from app import store
from app.vault import audit


def _fresh():
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)
    store.init_db()


def test_chain_verifies_when_intact():
    _fresh()
    audit.append("seal", ["system"], "rec1", "captured")
    audit.append("breakglass_unlock", ["police", "judiciary"], "rec1", "warrant")
    assert audit.verify_chain() is True


def test_chain_detects_tampering():
    _fresh()
    audit.append("seal", ["system"], "rec1", "captured")
    audit.append("breakglass_unlock", ["police"], "rec1", "warrant")
    c = sqlite3.connect(store.DB_PATH)
    c.execute("UPDATE audit SET reason='altered' WHERE action='breakglass_unlock'")
    c.commit(); c.close()
    assert audit.verify_chain() is False
