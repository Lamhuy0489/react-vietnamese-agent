#!/usr/bin/env python3
"""Explicitly download a pinned public guard; preserve partial failures, no inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import ssl
import time
import urllib.request
from pathlib import Path

from react_agent.llm.guard_acquisition_v1 import (
    UpstreamSnapshot,
    verify_acquisition,
    verify_upstream_file,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ca-bundle", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/guard_models"):
        raise ValueError("fresh build/guard_models output required")
    pin_path = ROOT / "configs/guard_hf_v1/qwen_1_5b_upstream.json"
    upstream = UpstreamSnapshot.model_validate_json(pin_path.read_text())
    context = ssl.create_default_context(cafile=str(args.ca_bundle) if args.ca_bundle else None)
    total = sum(f.size for f in upstream.files)
    if shutil.disk_usage(ROOT).free < total + 1024**3:
        raise ValueError("insufficient disk headroom")
    snapshot = output / "snapshot"
    snapshot.mkdir(parents=True)
    partial = output / "partial"
    partial.mkdir()
    started = time.perf_counter()
    downloaded = []
    for entry in upstream.files:
        path = partial / entry.name
        print("Downloading " + entry.name, flush=True)
        try:
            # URL is constructed solely from the typed publisher inventory.
            with urllib.request.urlopen(  # noqa: S310 - typed inventory constructs HTTPS only
                upstream.url(entry), context=context, timeout=60
            ) as response:
                with path.open("xb") as stream:
                    count = 0
                    while block := response.read(1024 * 1024):
                        count += len(block)
                        if count > entry.size:
                            raise ValueError("download exceeds pinned size")
                        stream.write(block)
                        if count % (64 * 1024**2) == 0:
                            print(f"  {count // 1024**2} MiB", flush=True)
                    stream.flush()
                    os.fsync(stream.fileno())
            digest = verify_upstream_file(path, entry)
            path.rename(snapshot / entry.name)
            downloaded.append({"name": entry.name, "size": entry.size, "sha256": digest})
        except (
            Exception
        ) as error:  # Sanitized transport boundary; retain partial bytes for diagnosis.
            (output / "failure.json").write_text(
                json.dumps(
                    {
                        "valid": False,
                        "file": entry.name,
                        "error_class": type(error).__name__,
                        "completed_files": downloaded,
                        "automatic_retry": False,
                    },
                    indent=2,
                )
                + "\n"
            )
            print("ACQUISITION_FAILED: " + type(error).__name__, flush=True)
            return 1
    pin = verify_acquisition(snapshot, upstream)
    (output / "snapshot.json").write_text(pin.model_dump_json(indent=2) + "\n")
    receipt = {
        "schema_version": "phase5_guard_acquisition_v1",
        "valid": True,
        "upstream": upstream.model_dump(mode="json"),
        "upstream_pin_sha256": hashlib.sha256(pin_path.read_bytes()).hexdigest(),
        "snapshot_sha256": pin.sha256,
        "model_revision": pin.model_revision,
        "local_snapshot": snapshot.relative_to(ROOT).as_posix(),
        "files": downloaded,
        "bytes": total,
        "elapsed_seconds": time.perf_counter() - started,
        "tls_verified": True,
        "automatic_retry": False,
        "real_model_runs": 0,
    }
    (output / "acquisition.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"valid": True, "files": len(downloaded), "bytes": total}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
