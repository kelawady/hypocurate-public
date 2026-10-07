"""A local stand-in for the model provider's HTTP API (step 8a), for tests only.

litellm sends its real HTTP request to it (`client_options(stub)` gives the address and a dummy key),
so the tests see the actual outbound request as bytes, exactly as the provider would, and replay
scripted replies in the provider's format: a text answer with usage, an error status, a timeout, a
missing usage, a refusal, a tool call, a truncated answer. Nothing leaves the machine.

`on_request(callback)` runs a callback while a request is being served (for example to check that the
caller holds no open database transaction at that moment).
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DUMMY_KEY = "stub-key-not-a-secret"


def reply(text, *, input_tokens=1200, output_tokens=150, cache_read=0, cache_write=0, stop="end_turn"):
    return {"kind": "json", "status": 200, "body": {
        "id": "msg_stub", "type": "message", "role": "assistant", "model": "stub",
        "content": [{"type": "text", "text": text}], "stop_reason": stop, "stop_sequence": None,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens,
                  "cache_read_input_tokens": cache_read, "cache_creation_input_tokens": cache_write}}}


def error(status, kind, message="stub error"):
    return {"kind": "json", "status": status, "body": {"type": "error", "error": {"type": kind, "message": message}}}


def timeout(seconds):
    return {"kind": "sleep", "seconds": seconds}


def no_usage(text):
    r = reply(text)
    del r["body"]["usage"]
    return r


def refusal():
    r = reply("")
    r["body"]["content"] = []
    r["body"]["stop_reason"] = "refusal"
    return r


def tool_call():
    r = reply("")
    r["body"]["content"] = [{"type": "tool_use", "id": "toolu_1", "name": "read_file", "input": {"path": "/etc/x"}}]
    r["body"]["stop_reason"] = "tool_use"
    return r


def fields(**values) -> str:
    """An answer in DSPy's ChatAdapter form."""
    return "".join(f"[[ ## {k} ## ]]\n{v}\n\n" for k, v in values.items()) + "[[ ## completed ## ]]"


class StubProvider:
    def __init__(self):
        self.requests: list[dict] = []
        self.script: deque = deque()
        self._callback = None
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("content-length", 0)))
                stub.requests.append({"path": self.path, "headers": dict(self.headers), "raw": raw})
                if stub._callback:
                    stub._callback()
                step = stub.script.popleft() if stub.script else error(500, "api_error", "no scripted reply")
                if step["kind"] == "sleep":
                    time.sleep(step["seconds"])
                    step = reply("too late")
                body = json.dumps(step["body"]).encode()
                self.send_response(step["status"])
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self.base_url = f"http://127.0.0.1:{self._server.server_address[1]}"

    def queue(self, *steps):
        self.script.extend(steps)
        return self

    def on_request(self, callback):
        self._callback = callback

    def bodies(self) -> list[dict]:
        return [json.loads(r["raw"]) for r in self.requests]

    def close(self):
        self._server.shutdown()
        self._server.server_close()


def client_options(stub: StubProvider, timeout_seconds: float = 30) -> dict:
    return {"api_base": stub.base_url, "api_key": DUMMY_KEY, "timeout": timeout_seconds}
