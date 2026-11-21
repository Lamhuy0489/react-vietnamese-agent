#!/usr/bin/env python3
"""Launcher for BrokerGuard demo web UI."""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

from react_agent.demo.app import build_app  # noqa: E402
from react_agent.demo.config import DemoConfig  # noqa: E402
from react_agent.demo.session import DemoSession  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chạy ứng dụng web demo BrokerGuard.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Địa chỉ host phục vụ (mặc định 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7860, help="Cổng chạy ứng dụng (mặc định 7860)")
    parser.add_argument(
        "--share",
        action="store_true",
        help="Bật chia sẻ qua Gradio public link (yêu cầu DEMO_AUTH_USER và DEMO_AUTH_PASSWORD)",
    )
    parser.add_argument(
        "--env-file",
        default=".env.demo",
        help="Tệp cấu hình biến môi trường (mặc định .env.demo trong repo root)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chạy ở chế độ giả lập nội bộ (DEMO_DRY_RUN=1), không yêu cầu endpoint mô hình",
    )
    return parser.parse_args()


def check_model_endpoint(base_url: str, api_key: str, timeout: float = 10.0) -> None:
    """Validate connectivity to the OpenAI-compatible model endpoint."""
    if not base_url:
        print(
            "Lỗi: Biến môi trường VLLM_BASE_URL chưa được thiết lập. "
            "Vui lòng thiết lập trong .env.demo hoặc chạy với cờ --dry-run.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not base_url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
        print("Lỗi: VLLM_BASE_URL phải là https:// hoặc http://127.0.0.1.", file=sys.stderr)
        sys.exit(2)
    url = f"{base_url.rstrip('/')}/models"
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers, method="GET")  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310
            if response.status >= 400:
                print(
                    f"Lỗi: Endpoint mô hình trả về mã lỗi HTTP {response.status} khi gọi {url}.",
                    file=sys.stderr,
                )
                sys.exit(2)
    except urllib.error.HTTPError as exc:
        print(
            f"Lỗi: Endpoint mô hình trả về mã lỗi HTTP {exc.code} khi gọi {url}.",
            file=sys.stderr,
        )
        sys.exit(2)
    except urllib.error.URLError as exc:
        print(
            f"Lỗi: Không thể kết nối tới endpoint mô hình ({url}): {exc.reason}.",
            file=sys.stderr,
        )
        sys.exit(2)
    except TimeoutError:
        print(
            f"Lỗi: Hết thời gian chờ ({timeout:.0f}s) khi kết nối tới endpoint mô hình ({url}).",
            file=sys.stderr,
        )
        sys.exit(2)
    except Exception as exc:  # noqa: BLE001 - any failure means: do not start
        print(
            f"Lỗi: Kiểm tra endpoint mô hình ({url}) thất bại: {type(exc).__name__}.",
            file=sys.stderr,
        )
        sys.exit(2)


def main() -> None:
    args = parse_args()

    env_path = Path(args.env_file)
    if not env_path.is_absolute():
        env_path = REPO_ROOT / env_path
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path)

    if args.dry_run:
        os.environ["DEMO_DRY_RUN"] = "1"

    is_dry_run = os.environ.get("DEMO_DRY_RUN", "0") == "1"

    if not is_dry_run:
        base_url = os.environ.get("VLLM_BASE_URL", "").strip()
        api_key = os.environ.get("VLLM_API_KEY", "").strip()
        check_model_endpoint(base_url, api_key)

    auth: tuple[str, str] | None = None
    if args.share:
        user = os.environ.get("DEMO_AUTH_USER", "").strip()
        password = os.environ.get("DEMO_AUTH_PASSWORD", "").strip()
        if not user or not password:
            print(
                "Lỗi: Khi bật cờ --share, bắt buộc phải thiết lập cả DEMO_AUTH_USER và "
                "DEMO_AUTH_PASSWORD để bảo mật hệ thống. Từ chối khởi chạy chia sẻ.",
                file=sys.stderr,
            )
            sys.exit(1)
        auth = (user, password)

    config = DemoConfig.from_env()
    session = DemoSession(config)
    app = build_app(session)

    launch_kwargs: dict[str, Any] = {
        "server_name": args.host,
        "server_port": args.port,
        "share": args.share,
    }
    if auth is not None:
        launch_kwargs["auth"] = auth

    app.launch(**launch_kwargs)


if __name__ == "__main__":
    main()
