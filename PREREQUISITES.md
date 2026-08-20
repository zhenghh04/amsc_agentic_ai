# Prerequisites for Part 3 (Orchestrating via IRI)

This file is for **Part 3** — the local-laptop-plus-MCP-server way of reaching
Polaris, Perlmutter, and Frontier ([part3_iri/README.md](part3_iri/README.md)
has the full intro). If you're doing **Part 2** (running `claude` directly on a
login node) instead, skip this file entirely — [Lab 05](part2_hpc/05_native_on_your_system.md)
states its own, much lighter prerequisite (just an interactive account on one
system).

Part 1 needed only a laptop + a MAG token. **Part 3 submits real jobs and charges
a real allocation**, so it needs facility access and one extra piece of setup:
the **IRI MCP servers** that let the agent reach each facility's APIs.

> **You do not need all three facilities.** Everything in Part 3 works with an
> account and allocation on **any one** of Polaris, Perlmutter, or Frontier. Set
> up the one(s) you have; the labs point out which server serves which system.
> Option A of this tutorial ships all three so a multi-facility user can run the
> capstone across all of them.

Work through this once before starting [Lab 07](part3_iri/07_mcp_setup_and_explore.md).

---

## 0. Python and the server dependencies (do this first)

The three IRI servers and the `scripts/auth/` helpers are small Python programs.
They need **Python 3.10+** and three packages. Install them once — ideally into a
virtual environment so `python` resolves to the right interpreter:

```bash
cd amsc_agentic_ai
python3 -m venv .venv && source .venv/bin/activate   # recommended
pip install -r requirements.txt
```

`requirements.txt` pulls in `mcp` (the MCP server framework), `httpx` (the async
HTTP client the servers use), and `globus-sdk` (the browser login flow in the auth
scripts). Skip this and the auth scripts fail with `ModuleNotFoundError: No module
named 'globus_sdk'`, and the servers never appear in `/mcp`.

> **`python` vs `python3`.** `.mcp.json` launches each server with `python`. Inside
> an activated venv (above) that's correct. If you don't use a venv and your system
> only has `python3`, either create the venv or change the three `command` fields in
> [`.mcp.json`](.mcp.json) to `python3`.

## 1. An account and a compute allocation (on at least one system)

| System | Facility | Where to check your projects/allocation |
| --- | --- | --- |
| **Polaris** | ALCF | <https://my.alcf.anl.gov> → *Projects* |
| **Perlmutter** | NERSC | <https://iris.nersc.gov> → *Roles* / *Projects* |
| **Frontier** | OLCF | <https://my.olcf.ornl.gov> → *Projects* |

Your **allocation / project** is your scheduler account (PBS `-A` on Polaris,
Slurm `--account` / `-A` on Perlmutter and Frontier). Jobs charge node-hours to
it. No allocation? Ask your PI, or apply through the facility's allocations
program. You cannot do Part 3 without one on at least one system.

## 2. Credentials the tools will use

The agent's tools authenticate as **you**. The token you need depends on the
facility. This tutorial folder bundles small, self-contained scripts under
`scripts/auth/`. Run the one(s) for the facility you'll use, from inside
`amsc_agentic_ai/`:

```bash
# --- ALCF / Polaris — browser Globus login (IRI submit/monitor, list/read files)
python scripts/auth/alcf_iri_token.py authenticate

# --- NERSC / Perlmutter — browser Globus login (must log in via nersc.gov)
python scripts/auth/nersc_iri_token.py authenticate

# --- Globus Transfer token — move data to/from any facility's filesystems
python scripts/auth/globus_auth.py authenticate
```

The ALCF and NERSC scripts each open a browser login (or, over SSH with no
browser, print a URL to open yourself and paste back an auth code). They write
their token into **`.env` in this folder** (`amsc_agentic_ai/.env` — *not*
anything shared or version-controlled; keep it out of git) and refresh it
automatically thereafter. Check the Globus status any time with
`python scripts/auth/globus_auth.py status`.

### OLCF / Frontier — a manually issued API token

OLCF's IRI does **not** use a browser Globus flow. Instead, mint a token in the
myOLCF portal and paste it into `.env` yourself:

1. Go to <https://my.olcf.ornl.gov> → *Projects* → **API Tokens**.
2. Generate a token **with the compute scope** (a token without it can read
   facility/status but returns HTTP 401 on any job submission).
3. Add it to `amsc_agentic_ai/.env`:
   ```bash
   echo "OLCF_IRI_TOKEN=<paste-the-token>" >> .env
   ```

The `olcf-iri` server re-reads `.env` on every call, so a refreshed token is
picked up without a restart. OLCF's IRI enclave has **no filesystem API** — file
moves on Frontier go through **Globus** (the shared token from Step 2 above).

## 2b. Your personal Globus endpoint (for laptop ↔ facility transfers)

To transfer files **to or from your own laptop or workstation** you need a
**Globus Connect Personal (GCP)** endpoint running on that machine. Skip this
sub-step if you only need facility-to-facility transfers (Step 4 of Lab 09
covers that alternative).

### Install Globus Connect Personal

1. Go to <https://www.globus.org/globus-connect-personal> and download the
   installer for your OS (macOS, Windows, or Linux).
2. Install and launch it. During setup, sign in with your Globus identity (the
   same one you used in Step 2).
3. GCP records your personal endpoint UUID in a local config file (the exact
   path varies by OS — macOS/Linux: `~/.globusonline/lta/client-id.txt`;
   Windows: `%APPDATA%\Globus Connect Personal\`). The Globus SDK discovers it
   automatically — **no `.env` edit is needed** as long as GCP is installed.

### Find your personal endpoint UUID (optional)

The tools auto-discover your UUID via the Globus SDK (it handles the
OS-specific path). If you ever need the UUID directly:

- **macOS/Linux:** `cat ~/.globusonline/lta/client-id.txt`
- **Windows:** open `%APPDATA%\Globus Connect Personal\` in Explorer
- **Any OS:** open <https://app.globus.org> → *Collections* → *Your
  Collections* — it is listed there

### Override (advanced)

If you are running the tutorial on a cluster login node without GCP installed —
or want to explicitly pin a particular collection — set the env var in `.env`:

```bash
echo "LOCAL_GLOBUS_ENDPOINT=<your-uuid>" >> .env
```

The server checks this var first, then falls back to the GCP config file, then
raises a clear error if neither is present.

> **GCP must be running** when a transfer involves your laptop. Globus can only
> reach your machine when GCP is active (the tray icon is running). Transfers to
> facility-to-facility paths work regardless.

## 3. The IRI MCP servers, configured in Claude Code

This is the new piece. You'll add the MCP servers that expose each facility's
**IRI + Globus** capabilities as tools — submit a job, check status, list/read
files, transfer data.

**Already provided.** This tutorial ships three working servers:

| Server | Talks to | Serves | Token env var |
| --- | --- | --- | --- |
| [`mcp/hpc/alcf_server.py`](mcp/hpc/alcf_server.py) | `api.alcf.anl.gov` | **Polaris** | `ALCF_IRI_TOKEN` |
| [`mcp/hpc/nersc_server.py`](mcp/hpc/nersc_server.py) | `api.iri.nersc.gov` | **Perlmutter** | `NERSC_IRI_TOKEN` |
| [`mcp/hpc/olcf_iri_server.py`](mcp/hpc/olcf_iri_server.py) | `amsc-moderate.s3m.olcf.ornl.gov` | **Frontier** | `OLCF_IRI_TOKEN` |

All three are wired up in [`.mcp.json`](.mcp.json) in this folder:

```json
{
  "mcpServers": {
    "alcf-iri": { "command": "python", "args": ["mcp/hpc/alcf_server.py"] },
    "nersc-iri": { "command": "python", "args": ["mcp/hpc/nersc_server.py"] },
    "olcf-iri": { "command": "python", "args": ["mcp/hpc/olcf_iri_server.py"] }
  }
}
```

No secrets go in this file — each server reads `amsc_agentic_ai/.env` itself at
startup (Step 2), and re-reads it on every `authenticate()` call so a refreshed
token is picked up without a restart. As long as `claude` is launched with
`amsc_agentic_ai/` as your working folder (`cd amsc_agentic_ai && claude`, or
`code amsc_agentic_ai` for the VS Code extension), all three are picked up
automatically — nothing to register by hand. A server whose token you haven't set
simply reports "not authenticated" when you first call it — harmless; set up only
the facilities you use.

> **Prefer an officially supported integration if your facility later ships
> one.** Ask the facility's user support whether a facility-blessed agent/MCP
> integration exists for your systems. Swapping it in is the same mechanism —
> replace the relevant entry above — the rest of Part 3 is written against tool
> behavior, not this specific file.

## 4. Verify the connection (read-only, free)

Inside `claude`, from `amsc_agentic_ai/`:

```text
/mcp
```

You should see **alcf-iri**, **nersc-iri**, and **olcf-iri**, each with tools
including `list_resources`, `get_system_status`, `list_projects`, `submit_job`,
`get_job_status`. Then:

> What compute resources are up right now at ALCF, NERSC, and OLCF, and what
> allocations do I have on each?

The agent calls each server's read-only `list_resources`/`get_system_status`
(no auth needed) and `list_projects` (needs the token). Those calls **cost
nothing** — no job is submitted. If a server asks you to authenticate first,
that's the `authenticate()` tool telling you Step 2 hasn't run for that facility
yet (or the token expired); follow what it prints.

> **Swapped in a different MCP server?** Its tool names may differ from the
> ones above. Throughout Part 3, prompts are in plain English and you judge
> success by the *outcome*; the exact tool the agent picks depends on your
> server.

---

## Cost & etiquette (read before submitting anything)

- **You spend real node-hours.** Every Part 3 lab notes an approximate cost.
  Keep test jobs to the **debug queue, 1 node, a few minutes**.
- **Confirm irreversible actions.** Deleting files or cancelling jobs should be
  explicit; keep the agent's "ask first" reflex on.
- **Clean up.** Cancel stuck jobs; don't leave anything running after a lab.

## Reference

| Facility | User docs | Allocations / projects | Support |
| --- | --- | --- | --- |
| ALCF (Polaris) | <https://docs.alcf.anl.gov> | <https://my.alcf.anl.gov> | support@alcf.anl.gov |
| NERSC (Perlmutter) | <https://docs.nersc.gov> | <https://iris.nersc.gov> | <https://help.nersc.gov> |
| OLCF (Frontier) | <https://docs.olcf.ornl.gov> | <https://my.olcf.ornl.gov> | help@olcf.ornl.gov |

When Steps 1–3 are done for at least one facility and the Step 4 read-only check
works, start [Part 3 → Lab 07](part3_iri/07_mcp_setup_and_explore.md).

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
