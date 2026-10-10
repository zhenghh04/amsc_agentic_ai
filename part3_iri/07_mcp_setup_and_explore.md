# Lab 07 — Connect to ALCF / NERSC / OLCF & Explore (Read-Only)

> **Part 3 · Orchestrating Job Submission via IRI · ~20–30 min · Cost: free (no jobs submitted)**
>
> Prereq: [PREREQUISITES.md](../PREREQUISITES.md) done — an account + allocation
> on at least one facility, and that facility's IRI MCP server authenticated.

Before spending a single node-hour, get comfortable with the agent's new reach —
now spanning **three** facilities. Every tool you use here is **read-only** and
free: facility status, system health, your allocations, and a look at your files.
This is also how you *verify* your setup works before it matters.

---

## Objectives

1. Authenticate to the IRI APIs and Globus Transfer for each facility you use.
2. Confirm the bundled `alcf-iri`, `nersc-iri`, and `olcf-iri` servers are
   connected and their tools available.
3. Read live status for Polaris, Perlmutter, and Frontier through the agent.
4. Find **your** allocations and the account name you'll submit against, per
   facility.
5. Look at your directories on the facilities you have — without leaving the editor.

## Step 1 — Authenticate

Run the auth scripts for each facility you have an account on. All commands are
run from inside `amsc_agentic_ai/` with your virtual environment active.

### ALCF / Polaris — IRI token (browser Globus login)

```bash
python scripts/auth/alcf_iri_token.py authenticate
```

A browser window opens at `auth.globus.org`. Log in with your ALCF Globus
identity, grant the requested scopes, and the script writes `IRI_TOKEN_ALCF` to
`amsc_agentic_ai/.env`. Over SSH (no browser)? It prints a URL — open it on
any machine, paste back the code.

> Already have `IRI_TOKEN_ALCF` from the DOE IRI session? Put that value in
> `.env` and skip this step — it's the same token under the same name. The
> servers also still accept the older `ALCF_IRI_TOKEN` spelling.

### NERSC / Perlmutter — IRI token (Globus, must use nersc.gov identity)

```bash
python scripts/auth/nersc_iri_token.py authenticate
```

Same browser flow, but Globus will prompt you to link a `nersc.gov` identity if
you haven't already. Writes `IRI_TOKEN_NERSC` to `.env`.

### OLCF / Frontier — manually issued API token

OLCF does not use a browser flow. Mint a token in the portal and paste it in:

1. Go to <https://my.olcf.ornl.gov> → *Projects* → **API Tokens**.
2. Generate a token **with the compute scope** (without it, status calls work
   but job submission returns HTTP 401).
3. Add it to `.env`:
   ```bash
   echo "IRI_TOKEN_OLCF=<paste-the-token>" >> .env
   ```

### Globus Transfer — move data to/from any facility

```bash
python scripts/auth/globus_auth.py authenticate
```

Writes `GLOBUS_TRANSFER_TOKEN` (and mirrors the IRI tokens into `.env` if they
are fresher). Check status any time with:

```bash
python scripts/auth/globus_auth.py status
```

> **Tokens refresh automatically.** Each MCP server re-reads `.env` on every
> call, so a token rotated by the auth script is picked up immediately — no
> server restart needed.

> **Only do the facility/facilities you have.** A server whose token you haven't
> set simply reports "not authenticated" — it does not block the servers for
> your other facilities.

## Step 2 — Confirm the connections

Inside `claude` (launched from `amsc_agentic_ai/`):

```text
/mcp
```

You should see **alcf-iri**, **nersc-iri**, and **olcf-iri**, each with tools
including `list_resources`, `get_system_status`, `list_projects`, `submit_job`,
`get_job_status`. If one is missing, `claude` was likely not launched from
inside `amsc_agentic_ai/` (where `.mcp.json` lives). A server that shows but
says "not authenticated" means Step 1 hasn't been run for that facility yet.

## Step 3 — Read status across all three facilities

> What's up right now at ALCF, NERSC, and OLCF? For each, give me the system
> status (Polaris, Perlmutter, Frontier) and note any outages or maintenance.

The agent calls each server's read-only tools (`list_resources` /
`get_system_status` / `list_incidents`) and summarizes. Nothing is charged.

**What just happened:** the exact same agent loop as Part 1 — read → reason →
answer — but the "tools" now reach three facilities' live status APIs. You're
looking at three machine rooms from one editor. Notice the agent picks the right
server per system without you naming it.

## Step 4 — Find your allocation on each facility

You can't submit without knowing which **account** to charge. Ask:

> Which projects/allocations do I have at each facility I'm set up for, and how
> much of each is remaining? Give me the exact account name I'd use as the
> scheduler account for Polaris, Perlmutter, and/or Frontier.

The agent calls `list_projects` / `get_project_allocations` on each authenticated
server. Note the account names — you'll use them in Lab 08.

**What just happened:** this is the read-only half of allocation discipline. The
"evidence" here is your real allocation balance on each system. Never guess an
account name — have the agent read it.

> **OLCF note.** If `olcf-iri`'s `list_projects` returns 401 but status works,
> your `IRI_TOKEN_OLCF` was issued **without the compute scope** — re-mint it from
> myOLCF with compute enabled (see [PREREQUISITES.md](../PREREQUISITES.md#olcf--frontier--a-manually-issued-api-token)).

## Step 5 — Look around your filesystems

> List my home directory on Polaris and my scratch/project space, and do the same
> for any of Perlmutter or Frontier I'm set up for. Just show me what's there —
> don't change anything.

- **ALCF (Polaris):** the agent uses the IRI filesystem tool (`list_directory`)
  or Globus (`globus_ls`) on `/eagle/<project>/…` or `/home/<you>`.
- **NERSC (Perlmutter):** filesystem/Globus on `/pscratch/sd/…`, `/global/homes/…`,
  or `/global/cfs/cdirs/…`.
- **OLCF (Frontier):** the IRI enclave has **no filesystem API** — the agent uses
  **Globus** (`globus_ls`) on the OLCF DTN for `/ccs/home/…` or Orion scratch.

> **Path styles differ by tool and facility.** Filesystem/Globus tools want
> storage-root paths; a compute-node job uses the mounted path. If a listing
> fails, ask the agent to try the other path form — a common first-time snag.

**What just happened:** you can now inspect DOE storage conversationally across
facilities. In Lab 08 you'll *move* data and run a job; today you're just reading.

---

## ✅ Checkpoint

- [ ] Auth scripts ran without error for each facility you use; tokens are in `.env`.
- [ ] `python scripts/auth/globus_auth.py status` shows valid Globus Transfer credentials.
- [ ] `/mcp` shows `alcf-iri`, `nersc-iri`, and `olcf-iri` (authenticated for the
      facilities you use).
- [ ] The agent reported live status for at least one of Polaris / Perlmutter /
      Frontier.
- [ ] You know your **account name(s)** and remaining allocation per facility.
- [ ] You listed a real directory on at least one facility.

Everything so far was free. Next you'll spend your first node-minute.

Continue to [Lab 08 — IRI Job Submission and Monitoring](08_iri_job_submission.md).

---

## Exercises

1. **Pick the right machine.** Ask: *"For a quick 1-node GPU test job, which of
   my facilities and which queue should I use, and what's the max walltime on that
   queue?"* Note the debug/short queue for Lab 08.
2. **Compare three status calls.** Ask the agent to put Polaris, Perlmutter, and
   Frontier side by side (up/down, current load if available). One prompt, three
   servers — the multi-facility payoff in miniature.
3. **Health, not just status.** For ALCF, ask it to check the filesystem health of
   your scratch space (`check_filesystem_health`). Read-only pre-flighting like
   this is how an agent de-risks a run.

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
