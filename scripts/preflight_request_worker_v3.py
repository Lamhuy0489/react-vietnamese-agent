"""Package the exact inference-only v3 candidate and rehearse in isolated stdlib Python."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

FILES = (
    "react_agent/__init__.py", "react_agent/serving/__init__.py",
    "react_agent/serving/structured_api_v1.py",
    "react_agent/serving/quiescent_engine_v3.py",
    "react_agent/serving/request_storage_v3.py",
    "react_agent/serving/request_lifecycle_v3.py",
    "react_agent/serving/request_http_v3.py",
    "react_agent/serving/request_worker_v3.py",
)

PROBE = r'''
import json,sys,threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
mount=Path(sys.argv[1]).resolve(); role=sys.argv[2]
sys.path.insert(0,str(mount))
from react_agent.serving.quiescent_engine_v3 import QuiescentEngine
from react_agent.serving.request_http_v3 import QuiescentHTTP
from react_agent.serving.request_worker_v3 import load_worker
from react_agent.serving.structured_api_v1 import ServiceError,canonical
entered,release=threading.Event(),threading.Event()
calls=[]
def generate(spec,stop):
 calls.append(spec.request_id)
 return {"synthetic":True}
def synchronize():
 entered.set()
 assert release.wait(3)
engine=QuiescentEngine(generate,synchronize)
key="synthetic-package-key-000000000000000000"
app=QuiescentHTTP(api_key=key,role=role,model="synthetic",root=mount/role,
 engine=engine,identity={"session_id":"synthetic","source_commit":"a"*40,
 "worker_sha256":"b"*64,"model_revision":"sha256:"+"c"*64})
boot=app.lifecycle.instance_id; auth="Bearer "+key
body={"request_id":"r1","model":"synthetic",
 "messages":[{"role":"user","content":"synthetic private prompt"}]}
try: app.dispatch("GET","/v1/requests/r1","wrong",boot)
except ServiceError as exc: assert exc.code=="UNAUTHORIZED"
else: raise AssertionError("missing auth")
with ThreadPoolExecutor(max_workers=1) as pool:
 future=pool.submit(app.dispatch,"POST","/v1/chat/completions",auth,boot,canonical(body).encode())
 try:
  assert entered.wait(2)
  pending,code=app.dispatch("POST","/v1/requests/r1/cancel",auth,boot)
  assert code==202 and pending["request"]["engine_active"]
  assert not pending["request"]["gpu_quiescence_attested"]
 finally: release.set()
 result,code=future.result(timeout=3)
assert code==409 and result["request"]["state"]=="CANCELLED"
assert result["request"]["gpu_quiescence_attested"] and result["request"]["durable"]
assert app.dispatch("POST","/v1/chat/completions",auth,boot,canonical(body).encode())==(result,code)
assert calls==["r1"]
body["request_id"]="r2"
assert app.dispatch("POST","/v1/chat/completions",auth,boot,canonical(body).encode())[1]==200
for path in app.lifecycle.root.glob("*.json"):
 assert "synthetic private prompt" not in path.read_text() and key not in path.read_text()
origins={}
for name,module in tuple(sys.modules.items()):
 if name=="react_agent" or name.startswith("react_agent."):
  origin=Path(module.__file__).resolve()
  assert origin.is_relative_to(mount), (name,str(origin))
  origins[name]=str(origin.relative_to(mount))
assert len(origins)==8
print(json.dumps({"role":role,"module_origins":origins,"auth":True,"cancel":True,
 "dedup":True,"fresh_request":True,"private_text_persisted":False,
 "native_model_loads":0,"real_gpu_quiescence_proven":False}))
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight(root: Path, output: Path) -> dict[str, object]:
    root, output = root.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name in FILES:
        source = root / "src" / name
        if source.is_symlink() or not source.is_file():
            raise ValueError("regular allowlisted source required")
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        hashes[name] = digest(target)
    archive = output / "worker.tar"
    with tarfile.open(archive, "w") as tar:
        for name in FILES:
            tar.add(output / "source" / name, arcname=name, recursive=False)
    probe = output / "probe.py"
    probe.write_text(PROBE)
    results = []
    for layout in ("archive", "expanded"):
        mount = output / layout
        if layout == "expanded":
            mount /= "kaggle-generated-directory"
        mount.mkdir(parents=True)
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            if (sorted(member.name for member in members) != sorted(FILES)
                    or any(not member.isfile() for member in members)):
                raise ValueError("unexpected archive entries")
            for member in members:
                stream = tar.extractfile(member)
                if stream is None:
                    raise ValueError("regular file required")
                target = mount / member.name  # Exact allowlist above excludes traversal.
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(stream.read())
                if digest(target) != hashes[member.name]:
                    raise ValueError("source hash mismatch")
        for role in ("agent", "guard"):
            result = subprocess.run(  # noqa: S603 - fixed isolated stdlib Python/probe argv
                [sys.executable, "-I", "-S", str(probe), str(mount), role],
                cwd=mount, env={k: v for k, v in os.environ.items() if k not in {
                    "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}},
                capture_output=True, text=True, check=True, timeout=20)
            row = json.loads(result.stdout)
            row["layout"] = layout
            results.append(row)
    receipt: dict[str, object] = {"scope": "inference-only candidate; no benchmark tools/data",
        "source_state": "working tree, not a committed deployment freeze",
        "source_sha256": hashes, "archive_sha256": digest(archive),
        "probe_sha256": digest(probe), "layouts": results,
        "native_model_loads": 0, "gpu_verified": False, "notebook_submitted": False}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = preflight(Path(__file__).resolve().parents[1], args.output)
    print(json.dumps({"layouts_passed": len(result["layouts"]),  # type: ignore[arg-type]
                      "gpu_verified": False}))


if __name__ == "__main__":
    main()
