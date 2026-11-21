from pathlib import Path

from fastapi.testclient import TestClient

from brokerguard_api.main import create_app
from brokerguard_api.settings import Settings


def test_spa_fallback_never_serves_files_outside_dist(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html>INDEX")
    (dist / "favicon.svg").write_text("<svg/>")
    (tmp_path / "secret.txt").write_text("SECRET")
    app = create_app(Settings(database=tmp_path / "app.db", frontend_dist=dist))
    with TestClient(app) as client:
        assert client.get("/c/42").text.endswith("INDEX")
        assert client.get("/favicon.svg").text == "<svg/>"
        for path in ("/..%2fsecret.txt", "/%2e%2e/secret.txt", "/assets/..%2f..%2fsecret.txt"):
            assert "SECRET" not in client.get(path).text
        assert client.get("/api/unknown").status_code == 404
