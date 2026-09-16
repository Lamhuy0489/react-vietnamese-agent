"""Source-isolated native CPU control or explicitly limited metadata rehearsal."""

from pathlib import Path
from typing import Any

from run_phase5_guard_language_native_v1 import main as original

from react_agent.llm.constrained_generate_cpu_v1 import probe
from react_agent.security_v1.guard_bare_json_v1 import bind


def main() -> None:
    # Reuse input/commit/fresh-root admission; the callback receives tokenizer.parent.
    def native(bundle: Path, tokenizer: Path, admission: dict[str, Any]) -> dict[str, Any]:
        return probe(bundle, tokenizer, admission, tokenizer.parent / "generation")

    bind(original, native_probe=native)()


if __name__ == "__main__":
    main()
