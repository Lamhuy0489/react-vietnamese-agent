"""Exercise exact standalone worker bytes in archive and expanded package layouts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
from pathlib import Path

PROBE = r'''
import json,runpy,sys
from pathlib import Path
from lmformatenforcer import JsonSchemaParser
from jsonschema import validate,ValidationError

p=Path(sys.argv[1]); m=runpy.run_path(str(p),run_name="cpu_preflight")
cfg=m["LAUNCH_CONFIG"]
assert cfg["role"] in ("agent","guard") and "api_key" not in cfg
assert cfg["worker_sha256"]==sys.argv[2]
samples=[(m["AGENT_SCHEMA"],{"action":{"name":"calculator","arguments":{"expression":"23*7+5"}}}),
 (m["AGENT_SCHEMA"],{"final_answer":{"answer":"166"}}),
 (m["GUARD_SCHEMA"],{"risk":"SAFE","labels":[],"confidence":"LOW"}),
 (m["GUARD_SCHEMA"],{"risk":"MALICIOUS","labels":m["LABELS"],"confidence":"HIGH"})]
for schema,value in samples:
 text=json.dumps(value,ensure_ascii=False)
 parser=JsonSchemaParser(schema)
 for char in text:
  assert char in parser.get_allowed_characters(), (char,parser.get_allowed_characters())
  parser=parser.add_character(char)
 assert parser.can_end()
 validate(value,schema)
try: validate({"final_answer":{"answer":166}},m["AGENT_SCHEMA"])
except ValidationError: pass
else: raise AssertionError("numeric answer accepted")
class Fake:
 def __init__(self): self.calls=0
 def generate(self,spec): self.calls+=1;return {"synthetic":True,"request_id":spec.request_id}
engine=Fake();service=m["Service"](cfg,engine,"synthetic-key")
body={"model":cfg["model"],"messages":[{"role":"user","content":"synthetic"}],"request_id":"r1"}
assert service.complete(body)==service.complete(body) and engine.calls==1
bad={**body,"seed":7}
try:service.complete(bad)
except m["ServiceError"] as e:assert e.code=="REQUEST_ID_CONFLICT"
else:raise AssertionError("id conflict accepted")
assert not service.authorized("Bearer wrong")
assert service.authorized("Bearer synthetic-key")
print(json.dumps({"role":cfg["role"],"schema_controls":len(samples),"idempotency":True,
                  "model_loads":0,"gpu_claim":False,"source_path":str(p)}))
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    prepared = json.loads((directory / "prepared.json").read_text())
    qa = directory / "preflight"
    qa.mkdir(exist_ok=False)
    probe = qa / "probe.py"
    probe.write_text(PROBE)
    results = []
    for role, record in prepared["roles"].items():
        archive = qa / f"{role}.tar"
        with tarfile.open(archive, "w") as tar:
            for name, expected in record["files"].items():
                path = directory / role / name
                if path.is_symlink() or digest(path) != expected:
                    raise ValueError("source hash/link mismatch")
                tar.add(path, arcname=name, recursive=False)
        for layout in ("archive", "expanded"):
            mount = qa / role / layout
            if layout == "expanded":
                mount /= "kaggle-generated-directory"
            mount.mkdir(parents=True)
            with tarfile.open(archive) as tar:
                for member in tar.getmembers():
                    if not member.isfile() or Path(member.name).name != member.name:
                        raise ValueError("unsafe archive")
                for member in tar.getmembers():
                    stream = tar.extractfile(member)
                    if stream is None:
                        raise ValueError("regular file required")
                    (mount / member.name).write_bytes(stream.read())
            meta = json.loads((mount / "kernel-metadata.json").read_text())
            for name, expected in record["files"].items():
                if digest(mount / name) != expected:
                    raise ValueError("expanded hash mismatch")
            result = subprocess.run(  # noqa: S603 - fixed isolated interpreter/probe argv
                [str(args.python.absolute()), "-I", str(probe), str(mount / meta["code_file"]),
                 record["cfg"]["worker_sha256"]], cwd=mount, text=True, capture_output=True,
                env={k: v for k, v in os.environ.items() if k not in {
                    "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}}, check=True)
            row = json.loads(result.stdout.strip().splitlines()[-1])
            row["layout"] = layout
            results.append(row)
    value = {"prepared_sha256": digest(directory / "prepared.json"), "layouts": results,
        "source_commit": prepared["source_commit"], "benchmark_inputs": [],
        "worker_tools": [], "scope": "inference-only server; tools/benchmark remain host-side",
        "native_model_loads": 0, "gpu_verified": False}
    with (directory / "preflight.json").open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"layouts_passed": len(results), "gpu_verified": False}))


if __name__ == "__main__":
    main()
