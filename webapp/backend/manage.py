#!/usr/bin/env python3
"""Account administration for BrokerGuard Workspace (run from the repository root).

  .venv/bin/python webapp/backend/manage.py create-admin --username huy \
      --display-name "Lâm Quang Huy"
  .venv/bin/python webapp/backend/manage.py create-invite --role viewer
  .venv/bin/python webapp/backend/manage.py reset-password --username huy

Passwords are read with getpass (never from arguments, so they stay out of shell history).
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "src")]

from brokerguard_api.db import Database  # noqa: E402
from brokerguard_api.roles import ROLE_LABELS_VI, Role  # noqa: E402
from brokerguard_api.security import (  # noqa: E402
    MIN_PASSWORD,
    create_invite,
    create_user,
    set_password,
)
from brokerguard_api.settings import Settings  # noqa: E402


def _read_password() -> str:
    first = getpass.getpass(f"Mật khẩu (ít nhất {MIN_PASSWORD} ký tự): ")
    if getpass.getpass("Nhập lại: ") != first:
        raise SystemExit("Hai lần nhập không khớp.")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    admin = sub.add_parser("create-admin")
    admin.add_argument("--username", required=True)
    admin.add_argument("--display-name", default="")
    user = sub.add_parser("create-user")
    user.add_argument("--username", required=True)
    user.add_argument("--display-name", default="")
    user.add_argument("--role", choices=[r.value for r in Role], required=True)
    invite = sub.add_parser("create-invite")
    invite.add_argument("--role", choices=[r.value for r in Role], required=True)
    invite.add_argument("--hours", type=float, default=72)
    reset = sub.add_parser("reset-password")
    reset.add_argument("--username", required=True)
    args = parser.parse_args(argv)

    db = Database(Settings.from_env().database)
    if args.command in ("create-admin", "create-user"):
        role = Role.ADMIN if args.command == "create-admin" else Role(args.role)
        created = create_user(db, args.username, args.display_name, _read_password(), role)
        db.audit(None, "cli.create_user", json.dumps({"username": created.username}))
        print(f"Đã tạo tài khoản {created.username} ({ROLE_LABELS_VI[created.role]}).")
    elif args.command == "create-invite":
        code = create_invite(db, Role(args.role), None, hours=args.hours)
        print(f"Mã mời ({ROLE_LABELS_VI[Role(args.role)]}, {args.hours:g} giờ): {code}")
    else:
        with db.connect() as c:
            row = c.execute("SELECT id FROM users WHERE username = ?",
                            (args.username,)).fetchone()
        if row is None:
            raise SystemExit("Không có tài khoản này.")
        set_password(db, row["id"], _read_password())
        db.audit(None, "cli.reset_password", json.dumps({"user_id": row["id"]}))
        print("Đã đặt lại mật khẩu, mọi phiên cũ đã bị đăng xuất.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
