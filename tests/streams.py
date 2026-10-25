"""Fictional provider replies as the event streams a streaming request receives."""

import json

import httpx


def as_stream(request: httpx.Request, reply: httpx.Response) -> httpx.Response:
    """The same fictional reply, sent as server-sent events when the request asked to stream."""
    body = json.loads(request.content or b"{}")
    if not body.get("stream") or reply.status_code != 200:
        return reply
    value = reply.json()
    if value.get("object") == "response":
        kind = {"incomplete": "response.incomplete", "failed": "response.failed"}.get(
            value.get("status"), "response.completed")
        events = [{"type": kind, "sequence_number": 0, "response": value}]
    else:
        events = chat_chunks(value)
    text = "".join(f"data: {json.dumps(event)}\n\n" for event in events) + "data: [DONE]\n\n"
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=text)


def chat_chunks(completion: dict) -> list[dict]:
    """A chat completion as its streamed chunks: the answer, then the usage on its own."""
    base = {key: completion[key] for key in ("id", "created", "model") if key in completion}
    chunks = [{**base, "object": "chat.completion.chunk", "choices": [{
        "index": choice["index"], "finish_reason": choice["finish_reason"],
        "delta": {key: value for key, value in choice["message"].items()
                  if key in ("role", "content", "refusal", "tool_calls")}}]}
        for choice in completion.get("choices", [])]
    if "usage" in completion:
        chunks.append({**base, "object": "chat.completion.chunk", "choices": [],
                       "usage": completion["usage"]})
    return chunks
