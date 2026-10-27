"""Standalone inference worker: role schemas, bounded decoding, no benchmark tools."""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import importlib.metadata
import json
import re
import secrets
import subprocess
import tempfile
import threading
import time
import urllib.request
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from react_agent.serving import public_llama_source_v1 as public_llama

PROFILE = "react-vn-structured-api-v1"
LIMIT = 262144
PINS = {"torch": "2.10.0", "transformers": "4.57.6", "tokenizers": "0.22.2", "accelerate": "1.12.0",
        "lm-format-enforcer": "0.11.3", "jsonschema": "4.25.1", "cryptography": "46.0.3"}
LABELS = ["instruction_override", "external_exfiltration", "unauthorized_action",
          "control_influence"]
TOOLS = ["doc_search", "doc_read", "db_query", "calculator", "cached_search",
         "cached_fetch", "send_email_mock", "post_webhook_mock"]


def object_schema(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}


AGENT_SCHEMA = {"anyOf": [object_schema({"action": object_schema({
    "name": {"type": "string", "enum": TOOLS}, "arguments": {"type": "object"}})}),
    object_schema({"final_answer": object_schema({"answer": {"type": "string",
                                                            "minLength": 1}})})]}
GUARD_SCHEMA = object_schema({"risk": {"type": "string", "enum": [
    "SAFE", "SUSPICIOUS", "MALICIOUS"]}, "labels": {"type": "array", "maxItems": 4,
    "items": {"type": "string", "enum": LABELS}},
    "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}})


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_object(raw: str) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs)
    canonical(value)
    if not isinstance(value, dict):
        raise ValueError("object required")
    return value


class ServiceError(Exception):
    def __init__(self, code: str, status: int = 422) -> None:
        super().__init__(code)
        self.code, self.status = code, status


@dataclass(frozen=True)
class Spec:
    request_id: str
    messages: list[dict[str, str]]
    schema: dict[str, Any]
    max_tokens: int
    seed: int


def admit(body: dict[str, Any], role: str, model: str) -> Spec:
    if set(body) - {"model", "messages", "max_tokens", "temperature", "seed", "stream",
                    "response_format", "request_id"}:
        raise ServiceError("UNSUPPORTED_PARAMETER", 400)
    if body.get("model") != model:
        raise ServiceError("MODEL_MISMATCH", 400)
    if body.get("stream", False) is not False or body.get("temperature", 0) != 0:
        raise ServiceError("GREEDY_NONSTREAM_REQUIRED", 400)
    budget = body.get("max_tokens", 128 if role == "guard" else 512)
    seed = body.get("seed", 42)
    if (type(budget) is not int or not 1 <= budget <= (128 if role == "guard" else 1024)
            or type(seed) is not int or not 0 <= seed < 2**32):
        raise ServiceError("INVALID_BUDGET_OR_SEED", 400)
    messages = body.get("messages")
    if (not isinstance(messages, list) or not 1 <= len(messages) <= 64 or any(
            not isinstance(m, dict) or set(m) != {"role", "content"}
            or m["role"] not in {"system", "user", "assistant"}
            or not isinstance(m["content"], str) for m in messages)):
        raise ServiceError("INVALID_MESSAGES", 400)
    schema = GUARD_SCHEMA if role == "guard" else AGENT_SCHEMA
    if "response_format" in body:
        value = body["response_format"]
        if (not isinstance(value, dict) or value.get("type") != "json_schema"
                or not isinstance(value.get("json_schema"), dict)
                or value["json_schema"].get("strict") is not True
                or not isinstance(value["json_schema"].get("schema"), dict)):
            raise ServiceError("STRICT_JSON_SCHEMA_REQUIRED", 400)
        candidate = value["json_schema"]["schema"]
        if role == "guard" and candidate != GUARD_SCHEMA:
            raise ServiceError("GUARD_SCHEMA_FIXED", 400)
        encoded = canonical(candidate)
        if len(encoded.encode()) > 32768 or '"$ref"' in encoded or '"$id"' in encoded:
            raise ServiceError("BOUNDED_INLINE_SCHEMA_REQUIRED", 400)
        validator = importlib.import_module("jsonschema").Draft202012Validator
        try:
            validator.check_schema(candidate)
        except importlib.import_module("jsonschema").SchemaError:
            raise ServiceError("INVALID_SCHEMA", 400) from None
        schema = candidate
    request_id = body.get("request_id", uuid.uuid4().hex)
    if not isinstance(request_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", request_id):
        raise ServiceError("INVALID_REQUEST_ID", 400)
    return Spec(request_id, messages, schema, budget, seed)


def fingerprint(mount: Path) -> dict[str, Any]:
    files = {}
    for path in sorted(mount.iterdir()):
        if path.suffix not in {".json", ".safetensors", ".model", ".txt", ".jinja"}:
            continue
        if path.is_symlink() or not path.is_file():
            raise ServiceError("INVALID_MODEL_FILE", 503)
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(4 * 1024 * 1024):
                hasher.update(chunk)
        files[path.name] = {"size": path.stat().st_size, "sha256": hasher.hexdigest()}
    if "config.json" not in files or not any(n.endswith(".safetensors") for n in files):
        raise ServiceError("MODEL_FILES_MISSING", 503)
    return {"files": files, "sha256": sha(canonical(files).encode()),
            "publisher_attested": False}


def resolve_model_mount(model_source: str, input_root: Path = Path("/kaggle/input")) -> Path:
    """Resolve an exact version in the namespaced or legacy Kaggle mount layout."""
    if not re.fullmatch(
        r"[a-z0-9_-]+/[a-z0-9_.-]+/transformers/[a-z0-9_.-]+/[1-9][0-9]*",
        model_source,
    ) or any(part in {".", ".."} for part in model_source.split("/")):
        raise ServiceError("INVALID_MODEL_SOURCE", 503)
    source = Path(model_source)
    candidates = (input_root / "models" / source, input_root.joinpath(*source.parts[1:]))
    matches = []
    for candidate in candidates:
        current = input_root
        for part in ("", *candidate.relative_to(input_root).parts):
            current = current / part
            if current.is_symlink():
                raise ServiceError("INVALID_MODEL_MOUNT_LINK", 503)
        if candidate.is_dir():
            matches.append(candidate)
    if len(matches) > 1:
        raise ServiceError("AMBIGUOUS_MODEL_MOUNT", 503)
    if not matches:
        # Public model paths only; never dump environment variables or credentials.
        print("MODEL_MOUNT_MISSING " + canonical({
            "source": model_source, "expected_paths": [str(p) for p in candidates],
            "input_directories": sorted(p.name for p in input_root.iterdir() if p.is_dir())
            if input_root.is_dir() else [],
        }), flush=True)
        raise ServiceError("EXACT_MODEL_MOUNT_MISSING", 503)
    return matches[0]


class HFEngine:
    def __init__(self, cfg: dict[str, Any], stop: threading.Event) -> None:
        self.cfg, self.stop = cfg, stop
        for name, version in PINS.items():
            if importlib.metadata.version(name).split("+")[0] != version:
                raise ServiceError("DEPENDENCY_MISMATCH", 503)
        torch, hf = importlib.import_module("torch"), importlib.import_module("transformers")
        if not torch.cuda.is_available() or torch.cuda.device_count() != 2:
            raise ServiceError("TWO_T4_REQUIRED", 503)
        if any("T4" not in torch.cuda.get_device_name(i) for i in range(2)):
            raise ServiceError("T4_REQUIRED", 503)
        for i in range(2):
            a = torch.ones((16, 16), dtype=torch.float16, device=f"cuda:{i}")
            if float((a @ a).sum().item()) != 4096:
                raise ServiceError("CUDA_TENSOR_CHECK_FAILED", 503)
        if cfg.get("model_acquisition") is not None:
            public_llama.validate_configuration(cfg)
            mount = public_llama.prepare_model()
        else:
            mount = resolve_model_mount(cfg["model_source"])
        identity = fingerprint(mount)
        self.tokenizer = hf.AutoTokenizer.from_pretrained(str(mount), local_files_only=True,
                                                         trust_remote_code=False)
        self.model = hf.AutoModelForCausalLM.from_pretrained(str(mount), local_files_only=True,
            trust_remote_code=False, torch_dtype=torch.float16, device_map="auto",
            max_memory={0: "13GiB", 1: "13GiB"}, attn_implementation="sdpa")
        if any(str(v) in {"cpu", "disk"} for v in self.model.hf_device_map.values()):
            raise ServiceError("CPU_OFFLOAD_REFUSED", 503)
        self.model.eval()
        integration = importlib.import_module("lmformatenforcer.integrations.transformers")
        self.tokenizer_data = integration.build_token_enforcer_tokenizer_data(self.tokenizer)
        self.eos = self.model.generation_config.eos_token_id
        if isinstance(self.eos, int):
            self.eos = [self.eos]
        if not self.eos:
            raise ServiceError("EOS_REQUIRED", 503)
        self.metadata = {"profile": PROFILE, "session_id": cfg["session_id"],
            "source_commit": cfg["source_commit"], "worker_sha256": cfg["worker_sha256"],
            "role": cfg["role"], "model_revision": "sha256:" + identity["sha256"],
            "model_fingerprint": identity, "model_path": str(mount),
            "gpu": "2x Tesla T4", "quantization": "FP16", "context_limit": 4096,
            "max_output_tokens": 128 if cfg["role"] == "guard" else 1024,
            "dependencies": {k: importlib.metadata.version(k) for k in (*PINS, "torch")},
            "capabilities": {"json_schema": True, "seed": True, "stream": False,
                             "idempotency_cache": 64, "token_counts_from_ids": True},
            "data": [{"id": cfg["model"], "object": "model"}], "object": "list"}
        # A GPU generation, not load success alone, is the readiness gate.
        warmup = Spec("warmup", [{"role": "user", "content": 'Return {"ready":true}.'}],
                      object_schema({"ready": {"type": "boolean"}}), 32, 42)
        self.generate(warmup)

    def generate(self, spec: Spec) -> dict[str, Any]:
        torch, hf = importlib.import_module("torch"), importlib.import_module("transformers")
        lmfe = importlib.import_module("lmformatenforcer")
        integration = importlib.import_module("lmformatenforcer.integrations.transformers")
        # No fallback prompt or hidden system policy; the host owns its messages.
        prompt = self.tokenizer.apply_chat_template(spec.messages, tokenize=False,
            add_generation_prompt=True, enable_thinking=False)
        inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        prompt_tokens = int(inputs["input_ids"].shape[-1])
        if prompt_tokens > 4096:
            raise ServiceError("CONTEXT_LIMIT", 400)
        inputs = inputs.to(self.model.get_input_embeddings().weight.device)
        prefix = integration.build_transformers_prefix_allowed_tokens_fn(
            self.tokenizer_data, lmfe.JsonSchemaParser(spec.schema))
        started = time.monotonic()
        stop_event = self.stop

        class Stop(hf.StoppingCriteria):  # type: ignore[misc, name-defined]
            def __call__(self, *_: Any, **__: Any) -> bool:
                return stop_event.is_set() or time.monotonic() - started > 90

        torch.manual_seed(spec.seed)
        torch.cuda.manual_seed_all(spec.seed)
        generation = hf.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            repetition_penalty=1.0, max_new_tokens=spec.max_tokens,
            eos_token_id=self.eos, pad_token_id=self.tokenizer.eos_token_id)
        with torch.inference_mode():
            output = self.model.generate(**inputs, generation_config=generation,
                prefix_allowed_tokens_fn=prefix,
                stopping_criteria=hf.StoppingCriteriaList([Stop()]))
        tokens = output[0, prompt_tokens:].tolist()
        elapsed = time.monotonic() - started
        if stop_event.is_set():
            raise ServiceError("CANCELLED", 503)
        if elapsed > 90:
            raise ServiceError("GENERATION_TIMEOUT", 504)
        if not tokens or tokens[-1] not in self.eos:
            raise ServiceError("OUTPUT_LIMIT")
        text = self.tokenizer.decode(tokens, skip_special_tokens=True)
        try:
            value = json_object(text)
            importlib.import_module("jsonschema").validate(value, spec.schema)
        except (ValueError, importlib.import_module("jsonschema").ValidationError):
            raise ServiceError("OUTPUT_SCHEMA_FAILED") from None
        return {"id": "chatcmpl-" + spec.request_id, "object": "chat.completion",
            "model": self.cfg["model"], "model_revision": self.metadata["model_revision"],
            "session_id": self.cfg["session_id"], "profile": PROFILE,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": len(tokens),
                      "total_tokens": prompt_tokens + len(tokens)},
            "execution": {"schema_sha256": sha(canonical(spec.schema).encode()),
                          "seed": spec.seed, "decode_seconds": elapsed,
                          "thinking": False, "constrained_decoding": True}}


class Service:
    def __init__(self, cfg: dict[str, Any], engine: Any, key: str) -> None:
        self.cfg, self.engine, self._key = cfg, engine, key
        self.lock = threading.Lock()
        self.cache: OrderedDict[str, tuple[str, dict[str, Any], int]] = OrderedDict()

    def authorized(self, header: str) -> bool:
        return hmac.compare_digest(header, "Bearer " + self._key)

    def complete(self, body: dict[str, Any]) -> tuple[dict[str, Any], int]:
        spec = admit(body, self.cfg["role"], self.cfg["model"])
        digest = sha(canonical(body).encode())
        if not self.lock.acquire(blocking=False):
            raise ServiceError("BUSY", 429)
        try:
            if spec.request_id in self.cache:
                previous, result, status = self.cache[spec.request_id]
                if previous != digest:
                    raise ServiceError("REQUEST_ID_CONFLICT", 409)
                return result, status
            try:
                result, status = self.engine.generate(spec), 200
            except ServiceError as exc:
                result, status = {"error": {"code": exc.code}}, exc.status
            except Exception:  # Never return/log native exceptions or prompt/reasoning text.
                result, status = {"error": {"code": "GENERATION_FAILED"}}, 500
            self.cache[spec.request_id] = digest, result, status
            if len(self.cache) > 64:
                self.cache.popitem(last=False)
            return result, status
        finally:
            self.lock.release()


def serve(cfg: dict[str, Any]) -> None:
    stop = threading.Event()
    key = secrets.token_urlsafe(32)
    engine = HFEngine(cfg, stop)
    service = Service(cfg, engine, key)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_: Any) -> None:
            return

        def reply(self, value: dict[str, Any], status: int = 200) -> None:
            raw = canonical(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Completed result stays in the bounded request-id cache.

        def do_GET(self) -> None:
            if not service.authorized(self.headers.get("Authorization", "")):
                self.reply({"error": {"code": "UNAUTHORIZED"}}, 401)
            elif self.path == "/v1/models":
                self.reply(engine.metadata)
            else:
                self.reply({"error": {"code": "NOT_FOUND"}}, 404)

        def do_POST(self) -> None:
            if not service.authorized(self.headers.get("Authorization", "")):
                self.reply({"error": {"code": "UNAUTHORIZED"}}, 401)
                return
            if self.path == "/v1/shutdown":
                stop.set()
                self.reply({"status": "shutting_down"})
                return
            if self.path != "/v1/chat/completions":
                self.reply({"error": {"code": "NOT_FOUND"}}, 404)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= LIMIT:
                    raise ServiceError("REQUEST_SIZE", 413)
                self.connection.settimeout(10)
                body = json_object(self.rfile.read(size).decode())
                result, status = service.complete(body)
                self.reply(result, status)
            except ServiceError as exc:
                self.reply({"error": {"code": exc.code}}, exc.status)
            except (ValueError, OSError, RecursionError):
                self.reply({"error": {"code": "INVALID_REQUEST"}}, 400)

    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    temporary = tempfile.TemporaryDirectory(prefix="react-vn-tunnel-")
    binary = Path(temporary.name) / "cloudflared"
    urllib.request.urlretrieve(cfg["cloudflared_url"], binary)  # noqa: S310 - pinned release URL
    if sha(binary.read_bytes()) != cfg["cloudflared_sha256"]:
        raise ServiceError("TUNNEL_BINARY_HASH", 503)
    binary.chmod(0o700)
    tunnel = subprocess.Popen(  # noqa: S603 - verified executable and fixed args
        [str(binary), "tunnel", "--url", "http://127.0.0.1:8000", "--no-autoupdate"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    def discover() -> None:
        assert tunnel.stdout is not None  # noqa: S101 - PIPE is explicitly configured
        published = False
        for line in tunnel.stdout:
            match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if not match or published:
                continue
            # Only ciphertext leaves the private worker; the private key stays local.
            serialization = importlib.import_module("cryptography.hazmat.primitives.serialization")
            padding = importlib.import_module("cryptography.hazmat.primitives.asymmetric.padding")
            hashes = importlib.import_module("cryptography.hazmat.primitives.hashes")
            public = serialization.load_pem_public_key(cfg["public_key_pem"].encode())
            plaintext = canonical({"endpoint": match.group(0) + "/v1", "api_key": key,
                                   "session_id": cfg["session_id"]}).encode()
            encrypted = public.encrypt(plaintext, padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
            request = urllib.request.Request(  # noqa: S310 - fixed HTTPS notification host
                "https://ntfy.sh/" + cfg["topic"], data=canonical({
                    "session_id": cfg["session_id"], "ciphertext": base64.b64encode(
                        encrypted).decode()}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=15):  # noqa: S310 - fixed HTTPS host
                pass
            published = True
            print("READY " + cfg["model"] + " session=" + cfg["session_id"], flush=True)

    threading.Thread(target=discover, daemon=True).start()
    try:
        stop.wait(timeout=cfg.get("lifetime_seconds", 28800))
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        tunnel.terminate()
        try:
            tunnel.wait(timeout=10)
        except subprocess.TimeoutExpired:
            tunnel.kill()
            tunnel.wait()
        print("STOPPED " + cfg["model"], flush=True)
        temporary.cleanup()


def install_and_serve(cfg: dict[str, Any]) -> None:
    import sys

    subprocess.run(  # noqa: S603 - exact dependency pins, no shell
        [sys.executable, "-m", "pip", "install", "--quiet",
         *(f"{k}=={v}" for k, v in PINS.items())], check=True)
    print("LOADING " + cfg["model"], flush=True)
    serve(cfg)
