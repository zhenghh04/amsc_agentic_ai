# Bonus B — Under the hood: the chat-completion → agent loop

> **Going Further · optional · ~25 min · Cost: a few MAG tokens per run (cents)**
>
> Prereq: [Lab 00](../part1_fundamentals/00_setup_claude_mag.md) done — you have a
> MAG PAT in `AMSC_I2_API_KEY`. This page is an *explainer*, not a lab.

Bonus A opened up the MCP tool layer. This page opens up the *other* black box:
**the agent itself.** Claude Code and opencode feel like magic, but an agent is a
small, legible thing — an LLM plus a loop of ordinary code. By the end of this page
you could write one.

This mirrors the ALCF **Service-Enabled Science** workshop's
`03_ALCF_Inference_Service` demo, adapted to point at **MAG** (the model endpoint
you set up in Lab 00) instead of ALCF's inference cluster — same loop, your
credentials. The upstream runnable scripts are at
[argonne-lcf/Service_Enabled_Science/03_ALCF_Inference_Service](https://github.com/argonne-lcf/Service_Enabled_Science/tree/main/03_ALCF_Inference_Service).

## 1. A chat completion is one HTTP round-trip

MAG speaks the **OpenAI Chat Completions** wire (the `/v1` endpoint — the same one
the opencode provider in [`opencode.jsonc`](../opencode.jsonc) uses). So the
standard `openai` client, pointed at MAG, just works:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://i2-api.genesis.american-science-cloud.org/v1",
    api_key=os.environ["AMSC_I2_API_KEY"],
)

resp = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[
        {"role": "system", "content": "You are a concise assistant for HPC users."},
        {"role": "user", "content": "In two sentences: what is a supercomputer?"},
    ],
)
print(resp.choices[0].message.content)
```

A conversation is just a list of **messages**, each with a `role`:

| Role | Who's talking |
|---|---|
| `system` | the app, setting ground rules |
| `user` | the human |
| `assistant` | the model's reply |
| `tool` | the result of a tool the harness ran |

The model is **stateless** — it remembers nothing between requests. Whoever calls
it has to re-send the whole message list every time. Hold on to that fact; it's
the key to the next section.

## 2. An agent is that call, in a loop, with tools

Give the model a list of **tools** it may call, then wrap the whole thing in a
loop. That loop — the **harness** — is the agent:

1. send the conversation (+ tool definitions) to the model,
2. if the model asks to call a tool, **run it** and append the result,
3. repeat until the model answers in plain text instead of calling a tool.

Here's a complete one. The tool it's given is the read-only facility call from
[Bonus A](A_raw_facility_rest.md) — so this tiny agent can actually answer "is
Polaris up?" by reaching ALCF:

```python
import json, os, sys, requests
from openai import OpenAI


def get_system_status(name: str) -> str:
    """The read-only Facility REST call from Bonus A, as a tool."""
    resources = requests.get("https://api.alcf.anl.gov/api/v1/status/resources").json()
    status = {r["name"].lower(): r["current_status"] for r in resources}
    return json.dumps({"name": name, "status": status.get(name.lower(), "no such system")})


TOOLS = [{"type": "function", "function": {
    "name": "get_system_status",
    "description": "Get the live status (up/down) of an ALCF system.",
    "parameters": {"type": "object",
                   "properties": {"name": {"type": "string"}},
                   "required": ["name"]},
}}]
TOOL_FUNCTIONS = {"get_system_status": get_system_status}

client = OpenAI(
    base_url="https://i2-api.genesis.american-science-cloud.org/v1",
    api_key=os.environ["AMSC_I2_API_KEY"],
)

question = sys.argv[1] if len(sys.argv) > 1 else "Is Polaris up right now?"
messages = [
    {"role": "system", "content": "You are a helpful ALCF assistant. Be brief."},
    {"role": "user", "content": question},
]

while True:
    msg = client.chat.completions.create(
        model="claude-sonnet-4-6", messages=messages, tools=TOOLS,
    ).choices[0].message
    messages.append(msg.model_dump(exclude_none=True))   # append the model's turn

    if not msg.tool_calls:          # plain-text answer -> we're done
        print(msg.content)
        break

    for call in msg.tool_calls:     # the model asked for a tool: run it, append result
        result = TOOL_FUNCTIONS[call.function.name](**json.loads(call.function.arguments))
        print(f"[tool] {call.function.name}({call.function.arguments}) -> {result}")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
```

That's the entire pattern. MAG's OpenAI-compatible endpoint translates the
`tools=` schema and the model's tool calls to and from whatever the underlying
model (here, Claude) speaks natively, so the loop is identical no matter which
model you pick.

## 3. Why context grows (and why that matters)

Because the model is stateless, step 1 re-sends the **whole** `messages` list every
iteration, and steps 2–3 only ever **append** to it:

```
Request #1   system + user                         └─► model: call get_system_status("Polaris")
Request #2   system + user + assistant + tool       └─► model: "Polaris is up."
             ▲ the assistant turn and the tool result from round 1, appended
```

Every tool call makes the next request bigger — more prompt tokens, slower, more
expensive — until it hits the model's context limit. **Managing that growth
(summarizing, dropping old turns, spawning sub-agents) is one of the central
problems in agent design**, and it's exactly what Claude Code is doing when it
"compacts" a long session.

## 4. So what *is* Claude Code, then?

This loop. Claude Code and opencode are this same read → call tool → observe →
repeat loop, plus:

- **many tools** instead of one (a shell, file read/write/edit, search, and — via
  `.mcp.json` / `opencode.jsonc` — the facility MCP servers you used in Part 3),
- **permissions** (it asks before destructive actions),
- **context management** (the compaction from §3),
- a **UI** and session persistence.

Everything you did in Parts 1–3 rode on top of this. The agent was never
magic — it was a stateless model and a loop, and now you've seen the loop.

> **Want the ALCF Inference Service instead of MAG?** Point the client at a cluster
> endpoint and use an inference token (Bonus A's token note):
> `base_url="https://inference-api.alcf.anl.gov/resource_server/<cluster>/api/v1"`,
> `api_key=<alcf-tokens get-token inference>`, and an ALCF-hosted model such as
> `gpt-oss-120b`. The loop is unchanged — that's the point.

#### 🧪 Try it yourself

Add a second tool — wrap the **job-submit** `POST` from Bonus A as a
`submit_job(...)` function, describe it in `TOOLS`, and register it in
`TOOL_FUNCTIONS`. Ask the agent to run a one-node job. The loop itself doesn't
change — that's the lesson. (It will now spend node-hours; keep it to the debug
queue.)

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
