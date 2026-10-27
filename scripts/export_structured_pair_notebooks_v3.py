"""Export frozen worker scripts as owner-operated notebooks; no remote actions."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from launch_structured_pair_v3 import (
    PROFILE,
    ROOT,
    _check_source_commit,
    _verify_package,
    canonical,
    digest,
    save,
)


def export(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("build/kaggle package required")
    prepared = json.loads((directory / "prepared.json").read_text())
    commit = prepared["source_commit"]
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("source freeze required before notebook export")
    _check_source_commit(commit)
    qa = json.loads((directory / "preflight_v3/receipt.json").read_text())
    expected_layouts = {(role, layout) for role in ("agent", "guard")
                        for layout in ("code_file_only", "expanded")}
    if (qa.get("prepared_sha256") != digest(directory / "prepared.json")
            or qa.get("profile") != PROFILE
            or {(r.get("role"), r.get("layout")) for r in qa.get("roles", [])}
            != expected_layouts):
        raise ValueError("exact package preflight required")
    output = directory / "owner_handoff"
    if output.exists():
        raise ValueError("notebook export must be fresh")
    for role, record in prepared["roles"].items():
        _verify_package(directory / role, record["files"])
    output.mkdir()
    rows = []
    for role, record in prepared["roles"].items():
        cfg = record["cfg"]
        owner = record["kernel"].split("/")[0]
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,49}", owner):
            raise ValueError("invalid owner")
        folder = output / (owner + "-" + role)
        folder.mkdir()
        source = (directory / role / record["code_file"]).read_text()
        title = cfg["model"] + " API (" + role + ")"
        guide = (
            f"# {title}\n\nChủ tài khoản dự kiến: `{owner}`. "
            f"Source freeze: `{commit}`.\n\n"
            "Đây là candidate đã kiểm CPU, chưa xác minh suy luận GPU thực tế. "
            "Chủ tài khoản tự vận hành bằng quota được cấp hợp lệ cho mình.\n\n"
            "1. Tạo notebook private và import file ipynb trong gói.\n"
            "2. Chọn GPU T4 x2, bật Internet.\n"
            f"3. Add Input đúng model version: `{cfg['model_source']}`. "
            "Nếu model yêu cầu chấp nhận điều khoản, chủ tài khoản tự thực hiện.\n"
            "4. Chạy cell một lần, chờ thông báo READY. "
            "Không chạy lại cell hoặc đổi source để xử lý lỗi; lưu thông báo lỗi trước.\n"
            "5. Báo người điều phối rằng worker READY để kiểm API từ local. "
            "Dừng session khi đợt thử nghiệm kết thúc; tối đa8giờ tự đóng.\n\n"
            "Không cần dán key Kaggle. Key API của worker sinh khi khởi động, "
            "chỉ gửi thông tin kết nối đã mã hóa về local; không in key trong output. "
            "Không gửi key qua chat. Private discovery key vẫn chỉ nằm ở máy local.\n"
        )
        name = cfg["model"] + "-api.ipynb"
        notebook = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                        "name": "python3"},
                "language_info": {"name": "python"},
                "react_vn": {"owner": owner, "role": role, "source_commit": commit,
                             "native_verified": False}},
            "cells": [{"cell_type": "markdown", "id": "read-first", "metadata": {},
                       "source": guide.splitlines(True)},
                      {"cell_type": "code", "id": "worker", "metadata": {},
                       "execution_count": None, "outputs": [], "source": source.splitlines(True)}]}
        save(folder / name, notebook)
        exported = json.loads((folder / name).read_text())
        if "".join(exported["cells"][1]["source"]) != source:
            raise ValueError("notebook code differs from preflighted script")
        compile(source, str(folder / name), "exec")
        metadata = json.loads((directory / role / "kernel-metadata.json").read_text())
        metadata.update(code_file=name, kernel_type="notebook")
        save(folder / "kernel-metadata.json", metadata)
        (folder / "README.md").write_text(guide)
        archive = output / (owner + "-" + role + ".zip")
        with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as bundle:
            for member in (name, "kernel-metadata.json", "README.md"):
                bundle.write(folder / member, member)
        rows.append({"role": role, "owner": owner, "requested_kernel": record["kernel"],
            "notebook": str((folder / name).relative_to(ROOT)),
            "notebook_sha256": digest(folder / name),
            "script_sha256": digest(directory / role / record["code_file"]),
            "archive": str(archive.relative_to(ROOT)), "archive_sha256": digest(archive)})
    receipt = {"schema": "owner_notebooks_v3_export_v1", "source_commit": commit,
        "prepared_sha256": digest(directory / "prepared.json"),
        "preflight_sha256": digest(directory / "preflight_v3/receipt.json"),
        "roles": rows, "notebook_code_matches_script": True,
        "network_actions": [], "private_discovery_key_shared": False,
        "submitted": False, "native_verified": False, "phase5_accepted": False}
    save(directory / "owner_handoff_receipt.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    result = export(args.directory)
    print(canonical({"source_commit": result["source_commit"], "notebooks": len(result["roles"]),
                     "submitted": False}))


if __name__ == "__main__":
    main()
