"""End-to-end API smoke test against the app, using an isolated temp database
so it never collides with a running backend instance."""
import time, warnings
warnings.filterwarnings("ignore")
from app import store


def test_full_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "api_test.db"))
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        time.sleep(3)
        assert c.get("/healthz").json()["status"] == "ok"
        assert c.get("/stats").status_code == 200
        assert isinstance(c.get("/alerts").json(), list)

        a1 = c.post("/ask", json={"question": "how many people in zone A?"}).json()
        a2 = c.post("/ask", json={"question": "who is the tallest person?"}).json()
        assert "people" in a1["answer"].lower()
        assert "only" in a2["answer"].lower()

        ps = c.get("/privacy-score").json()
        assert ps["attempts"] > 0 and ps["successful_reids"] == 0

        demo = c.get("/demo/records").json()
        rid = demo["alice"]["record_id"]; sh = demo["alice"]["holder_shares"]
        req = c.post("/breakglass/request",
                     json={"record_id": rid, "reason": "warrant", "requester": "police"}).json()
        r1 = c.post("/breakglass/share",
                    json={"request_id": req["request_id"], "holder_id": "police", "share": sh["police"]}).json()
        assert r1["status"] == "pending"
        r2 = c.post("/breakglass/share",
                    json={"request_id": req["request_id"], "holder_id": "judiciary", "share": sh["judiciary"]}).json()
        assert r2["status"] == "unlocked" and r2["revealed"]

        assert c.get("/audit/head").json()["verified"] is True
