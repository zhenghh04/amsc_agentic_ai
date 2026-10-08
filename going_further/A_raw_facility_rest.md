# Bonus A — Under the hood: the raw Facility REST API

> **Going Further · optional · ~20 min · Cost: free if you stop at the read-only
> calls; the submit example spends ~1 node-min**
>
> Prereq: you've done [Part 3](../part3_iri/README.md) (or at least
> [PREREQUISITES.md](../PREREQUISITES.md)) and have an ALCF IRI token. This page
> is an *explainer*, not a lab — there's nothing you must run.

In Part 3 you asked the agent to "submit a job on Polaris" and it called the
`alcf-iri` MCP tool `submit_job`. That tool is not magic: underneath, it makes one
ordinary HTTPS request to ALCF's **Facility (IRI) API**. This page shows you that
request, so the MCP layer stops being a black box.

This mirrors the ALCF **Service-Enabled Science** workshop's `01_Facility_API`
demo. The full, runnable scripts live upstream —
[argonne-lcf/Service_Enabled_Science/01_Facility_API](https://github.com/argonne-lcf/Service_Enabled_Science/tree/main/01_Facility_API).
The snippets below are abridged to show the shape, not to be copy-run; reach for
the upstream repo when you want to execute them.

## The one idea

An MCP tool is a thin wrapper over an HTTP call. `submit_job`, `get_job_status`,
`read_file` — each is a `GET` or `POST` to a URL under
`https://api.alcf.anl.gov/api/v1`, with your IRI token in an `Authorization`
header. The agent decides *which* tool with *which* arguments; the tool turns that
into the request below.

- API docs: <https://docs.alcf.anl.gov/services/iri-api/>
- Interactive Swagger: <https://api.alcf.anl.gov/>
- OpenAPI spec: <https://api.alcf.anl.gov/openapi.json>

## 1. Reading public status needs no token

System status is public. This is the HTTP behind "is Polaris up?":

```python
import requests

resources = requests.get("https://api.alcf.anl.gov/api/v1/status/resources").json()
for r in resources:
    print(r["name"], r["current_status"], r["id"])
```

Each resource has a stable `id` you address jobs and filesystem ops to:

| Resource | ID |
|---|---|
| Polaris | `55c1c993-1124-47f9-b823-514ba3849a9a` |
| Crux | `8b9b42f7-572a-4909-8472-a0453436304c` |
| Eagle (filesystem) | `1c3ad9d4-2e91-42bc-becb-72b1fde1235c` |
| Home (filesystem) | `6115bd2c-957a-4543-abff-5fae52992ff2` |

*(The API is under active development; resources and IDs can change — the
read-only `status/resources` call above is always the source of truth.)*

## 2. Submitting a job needs your token

Everything that acts as *you* — submitting, cancelling, reading your files —
carries a bearer token in the header. **This is the same token the `alcf-iri` MCP
server uses**; the server just re-reads it from `.env` on every call (see
[PREREQUISITES.md](../PREREQUISITES.md), "How it works"). In a standalone script
you'd read it from the environment:

```python
import os, requests

headers = {
    "Authorization": f"Bearer {os.environ['ALCF_IRI_TOKEN']}",
    "Content-Type": "application/json",
}

POLARIS = "55c1c993-1124-47f9-b823-514ba3849a9a"
resp = requests.post(
    f"https://api.alcf.anl.gov/api/v1/compute/job/{POLARIS}",
    headers=headers,
    json={
        "executable": "/bin/bash",
        "arguments": ["-lc", "whoami; hostname; echo done"],
        "name": "my-job",
        "stdout_path": "/home/<your-alcf-username>/log_example.out",
        "stderr_path": "/home/<your-alcf-username>/log_example.err",
        "resources": {"node_count": 1},
        "attributes": {
            "duration": 300,                 # walltime, seconds
            "queue_name": "debug",
            "account": "<your-allocation>",  # charged real node-hours
            "custom_attributes": {"filesystems": "home:eagle"},
        },
    },
)
print(resp.json())   # -> {"id": "<pbs-id>...", "status": {"state": "queued", ...}}
```

That JSON body is exactly the set of parameters the `submit_job` MCP tool exposes
as named arguments — `node_count`, `duration`, `queue_name`, `account`. Seeing the
raw request is the whole point: **the agent + MCP layer is a natural-language
front end over this.** The remaining `01_Facility_API` scripts (`get_job_state`,
`view_file`, `list_jobs`, `cancel_job`, `get_allocations`) are the same pattern at
different endpoints.

> ⚠️ The `status/resources` call is free. The `POST` above **submits a real job**
> and spends node-hours against `account`. Keep it to 1 node / debug queue, and
> fill in your real username and allocation first.

## A note on tokens — `alcf-tokens` vs. the bundled helpers

ALCF ships an official token manager, **[`alcf-tokens`](https://pypi.org/project/alcf-tokens/)**
(the upstream SES scripts use it). It's one CLI for all ALCF service tokens:

```bash
alcf-tokens login                   # Globus browser login, ALCF identity
alcf-tokens get-token iri           # print an IRI token (what the headers above need)
alcf-tokens test-token iri          # -> {"ready": true, "error": null}
alcf-tokens get-token inference     # a token for the ALCF Inference Service (Bonus B)
```
…and a Python entry point: `from alcf_tokens.auth import get_access_token, ServiceName`.

This tutorial bundles its **own** helpers instead
([`scripts/auth/alcf_iri_token.py`](../scripts/auth/alcf_iri_token.py),
`nersc_iri_token.py`, `globus_auth.py`). They are a deliberate complement, not a
competitor — the trade-off is narrow and worth understanding:

| | the bundled tutorial flow | `alcf-tokens` |
|---|---|---|
| Facilities | **ALCF + NERSC + Globus** via `scripts/auth/*.py` (+ OLCF via a manual portal token) | ALCF only |
| Where the token lands | writes it into **`.env`**, which every bundled MCP server re-reads per call | its own cache (`~/`), read via CLI/SDK |
| Extra dependency | none (vendored in this repo) | `pip install alcf-tokens` |
| Support | this tutorial | **officially supported by ALCF** |

The `.env` integration is the reason the tutorial bundles its own: the MCP servers
authenticate by re-reading `.env`, so a token has to land there. Guidance:

- **For this tutorial**, use the bundled helpers — cross-facility, zero extra deps,
  and already wired to the `.env` the MCP servers read.
- **Reach for `alcf-tokens`** when you're ALCF-only, want the officially-supported
  tool, or are following ALCF's own SES / Inference demos (which assume it).
- **They interoperate.** `alcf-tokens` manages the token; the MCP servers read it from
  `.env` (not your shell), so it has to land *there* — set the `ALCF_IRI_TOKEN=` line in
  `.env` to the CLI's output, e.g. append it with
  `echo "ALCF_IRI_TOKEN=$(alcf-tokens get-token iri)" >> .env` (replace an existing
  `ALCF_IRI_TOKEN=` line rather than leaving a duplicate). A plain shell
  `ALCF_IRI_TOKEN=…` assignment won't do — the servers never see your shell.

---

*Next:* [Bonus B — the chat-completion → agent loop](B_chat_completion_agent_loop.md)
shows the *other* black box: what Claude Code and opencode are actually doing when
they "think and call a tool."

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
