"""A scripted Anthropic-messages model server for the Claude Code tool-timeout self-test (no model server is used).

The first request that offers the Bash tool gets one Bash call: a 90 s loop that appends the time to
/logs/agent/probe-ticks every second (the trial's agent log folder on the host). Every other request gets the text
"Done.". Each request is logged (model name, stream, tools, last message) to the file given as argv[2].
    python scripted_messages.py <port> <log file>
Used by selftest-cc-timeout.yaml and selftest-cc-timeout-nobg.yaml (see there).
"""
import json
import sys
import time

from aiohttp import web

PROBE = "for i in $(seq 1 90); do date +%s >> /logs/agent/probe-ticks; sleep 1; done; echo finished"
LOG = open(sys.argv[2], "a")


def log(**kw):
    LOG.write(json.dumps({"ts": round(time.time(), 3), **kw}) + "\n")
    LOG.flush()


def sse(data):
    return f"event: {data['type']}\ndata: {json.dumps(data)}\n\n".encode()


async def messages(request):
    body = await request.json()
    tools = [t.get("name") for t in body.get("tools") or []]
    msgs = body.get("messages") or []
    used = any(isinstance(m.get("content"), list) and any(b.get("type") == "tool_use" for b in m["content"])
               for m in msgs if m.get("role") == "assistant")
    last = msgs[-1] if msgs else {}
    lc = last.get("content")
    log(model=body.get("model"), stream=bool(body.get("stream")), n=len(msgs), has_bash="Bash" in tools,
        last=(lc[:200] if isinstance(lc, str) else [{k: (str(v)[:300]) for k, v in b.items()} for b in lc or []]))
    if "Bash" in tools and not used:
        block = {"type": "tool_use", "id": f"toolu_probe{int(time.time())}", "name": "Bash",
                 "input": {"command": PROBE, "description": "Probe loop"}}
        stop = "tool_use"
    else:
        block = {"type": "text", "text": "Done."}
        stop = "end_turn"
    msg = {"id": f"msg_{int(time.time() * 1000)}", "type": "message", "role": "assistant", "model": body.get("model"),
           "content": [block], "stop_reason": stop, "stop_sequence": None,
           "usage": {"input_tokens": 100, "output_tokens": 20}}
    if not body.get("stream"):
        return web.json_response(msg)
    resp = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
    await resp.prepare(request)
    await resp.write(sse({"type": "message_start", "message": dict(msg, content=[], stop_reason=None)}))
    if block["type"] == "tool_use":
        await resp.write(sse({"type": "content_block_start", "index": 0, "content_block": dict(block, input={})}))
        text = json.dumps(block["input"])
        for piece in (text[:len(text) // 2], text[len(text) // 2:]):
            await resp.write(sse({"type": "content_block_delta", "index": 0,
                                  "delta": {"type": "input_json_delta", "partial_json": piece}}))
    else:
        await resp.write(sse({"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}))
        await resp.write(sse({"type": "content_block_delta", "index": 0,
                              "delta": {"type": "text_delta", "text": block["text"]}}))
    await resp.write(sse({"type": "content_block_stop", "index": 0}))
    await resp.write(sse({"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None},
                          "usage": {"output_tokens": 20}}))
    await resp.write(sse({"type": "message_stop"}))
    return resp


async def count_tokens(request):
    return web.json_response({"input_tokens": 100})


async def other(request):
    log(other=request.path, method=request.method)
    return web.json_response({"type": "error", "error": {"type": "not_found_error", "message": request.path}},
                             status=404)


app = web.Application(client_max_size=64 * 1024 * 1024)
app.router.add_post("/v1/messages", messages)
app.router.add_post("/v1/messages/count_tokens", count_tokens)
app.router.add_route("*", "/{tail:.*}", other)
web.run_app(app, host="127.0.0.1", port=int(sys.argv[1]))
