"""Build five synthetic prospective environments after the reviewed pin.

Only task/environment files are worker inputs. The condition source, casebook
and receipt remain host-side; no evaluator oracle is copied into environments.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from react_agent.environment.documents import Document
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.validation.clause_dev_release_v1 import digest
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.host_inventory_schema_v1 import InventoryPin
from react_agent.validation.room_inventory_review_v1 import RoomInventoryReview

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/smoke"
SPEC = ROOT / "data/prospective/room_v1/conditions.json"
PIN = ROOT / "experiments/manifests/phase5_room_prospective_inventory_pin_v1.json"
PIN_RECEIPT = ROOT / "experiments/manifests/phase5_room_prospective_pin_receipt_v1.json"
REVIEW = ROOT / "experiments/manifests/phase5_room_prospective_inventory_review_v1.json"
DRAFT = ROOT / "experiments/manifests/phase5_room_prospective_inventory_review_draft_v1.json"
CONDITIONS = (
    "clean_public_room",
    "poisoned_public_room",
    "s2_collision",
    "wrong_destination",
    "final_leak",
)
BASE_FILES = (
    "cached_pages/pages.json",
    "database/seed.json",
    "database/university.db",
)


def _admit_pin(package: Path) -> tuple[InventoryPin, dict[str, Any]]:
    for path in (BASE, SPEC, PIN, PIN_RECEIPT, REVIEW, DRAFT, package):
        no_links(path)
    review = RoomInventoryReview.model_validate_json(REVIEW.read_bytes())
    draft = DRAFT.read_bytes()
    pin = InventoryPin.model_validate_json(PIN.read_bytes())
    equal(
        pin.model_dump(mode="json"),
        review.prepare_pin(
            draft,
            source_commit=pin.source_commit,
            declared_at_utc=pin.declared_at_utc,
        ).model_dump(mode="json"),
        "reviewed prospective inventory pin",
    )
    receipt = json.loads(PIN_RECEIPT.read_text(encoding="utf-8"))
    for key, expected in {
        "source_commit": pin.source_commit,
        "inventory_pin_sha256": pin.identity,
        "inventory_pin_file_sha256": digest(PIN),
        "review_file_sha256": digest(REVIEW),
        "reviewed_draft_sha256": digest(DRAFT),
        "pilot_document_content_created": False,
    }.items():
        equal(receipt[key], expected, "pre-content pin receipt " + key)
    preflight = json.loads((package / "preflight.json").read_text(encoding="utf-8"))
    equal(preflight["source_commit"], pin.source_commit, "committed package source")
    equal(preflight["source_mode"], "committed", "committed package mode")
    equal(preflight["committed_source_admitted"], True, "committed package admission")
    equal(
        preflight["source_manifest_sha256"],
        receipt["source_manifest_sha256"],
        "pin-bound source manifest",
    )
    equal(
        digest(package / "source_manifest.json"),
        receipt["source_manifest_sha256"],
        "actual package source manifest",
    )
    if len(preflight["layouts"]) != 2 or not all(
        row["valid"] and row["committed_source_admitted"] for row in preflight["layouts"]
    ):
        raise ValueError("both committed package layouts required")
    return pin, receipt


def build(output: Path, package: Path) -> dict[str, Any]:
    no_links(output)
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle prospective output required")
    pin, receipt = _admit_pin(package)
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    equal(
        sorted(spec),
        ["conditions", "pair_id", "protocol", "scope", "task"],
        "prospective condition fields",
    )
    equal(spec["protocol"], "phase5_room_prospective_conditions_v1", "condition protocol")
    equal(spec["pair_id"], pin.annotations.pair_id, "condition pair")
    equal(spec["scope"], "new_synthetic_pilot_not_phase3_benchmark", "pilot scope")
    task = PublicWorkbenchTask.model_validate(spec["task"])
    cases = spec["conditions"]
    if not isinstance(cases, list) or tuple(row["id"] for row in cases) != CONDITIONS:
        raise ValueError("exact predeclared condition order required")
    base_docs = json.loads((BASE / "documents/documents.json").read_text(encoding="utf-8"))
    if not isinstance(base_docs, list) or any(
        row["doc_id"].startswith("AUX_") for row in base_docs
    ):
        raise ValueError("base environment already has auxiliary sources")
    for row in cases:
        if set(row) != {"id", "public_content", "private_content"} or not all(
            isinstance(row[key], str) and row[key] for key in ("public_content", "private_content")
        ):
            raise ValueError("exact nonempty public/private synthetic condition required")
        if "SECRETVALUE6042" not in row["private_content"] or "ROOM3176" not in row[
            "public_content"
        ]:
            raise ValueError("declared synthetic values changed")
    output.mkdir(parents=True)
    task_path = output / "task.json"
    task_path.write_text(
        json.dumps(task.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    built = []
    for row in cases:
        case_root = output / "conditions" / row["id"]
        environment = case_root / "environment"
        (environment / "documents").mkdir(parents=True)
        for name in BASE_FILES:
            target = environment / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BASE / name, target)
        documents = [Document.model_validate(item).model_dump(mode="json") for item in base_docs]
        for identity, title, content in (
            ("AUX_FUTUREPRIVATE", "Synthetic private record", row["private_content"]),
            ("AUX_FUTUREROOM", "Synthetic public room", row["public_content"]),
        ):
            documents.append(
                Document.model_validate(
                    {"doc_id": identity, "title": title, "content": content}
                ).model_dump(mode="json")
            )
        (environment / "documents/documents.json").write_text(
            json.dumps(documents, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        ids = [item["doc_id"] for item in documents]
        if len(ids) != len(set(ids)) or {item for item in ids if item.startswith("AUX_")} != {
            "AUX_FUTUREPRIVATE",
            "AUX_FUTUREROOM",
        }:
            raise ValueError("generated environment auxiliary inventory changed")
        built.append(
            {
                "condition": row["id"],
                "environment_sha256": text_hash(canonical_json(inventory(environment))),
                "document_file_sha256": digest(environment / "documents/documents.json"),
                "task_file_sha256": digest(task_path),
                "worker_inputs_only": True,
            }
        )
    result = {
        "protocol": "phase5_room_prospective_payload_receipt_v1",
        "source_commit": pin.source_commit,
        "source_manifest_sha256": receipt["source_manifest_sha256"],
        "inventory_pin_sha256": pin.identity,
        "inventory_pin_file_sha256": digest(PIN),
        "condition_source_sha256": digest(SPEC),
        "builder_sha256": digest(Path(__file__)),
        "task_sha256": digest(task_path),
        "cases": built,
        "held_out_test_loaded": False,
        "private_ground_truth_loaded": False,
        "native_inference_runs": 0,
        "phase5_accepted": False,
    }
    write_receipt(output / "payload_receipt.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output, args.package)
    print(
        json.dumps(
            {"protocol": result["protocol"], "cases": len(result["cases"]), "valid": True}
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
