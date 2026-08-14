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

1. Confirm the bundled `alcf-iri`, `nersc-iri`, and `olcf-iri` servers are
   connected and their tools available.
2. Read live status for Polaris, Perlmutter, and Frontier through the agent.
3. Find **your** allocations and the account name you'll submit against, per
   facility.
4. Look at your directories on the facilities you have — without leaving the editor.

## Step 1 — Confirm the connections

Inside `claude` (launched from `amsc_agentic_ai/`):

```text
/mcp
```

You should see **alcf-iri**, **nersc-iri**, and **olcf-iri**, each with tools
including `list_resources`, `get_system_status`, `list_projects`, `submit_job`,
`get_job_status`. If one is missing, most likely `claude` wasn't launched from
inside `amsc_agentic_ai/` (where `.mcp.json` lives). A server that *shows* but
says "not authenticated" just means you haven't set that facility's token — fine
if you don't use it.

## Step 2 — Read status across all three facilities

> What's up right now at ALCF, NERSC, and OLCF? For each, give me the system
> status (Polaris, Perlmutter, Frontier) and note any outages or maintenance.

The agent calls each server's read-only tools (`list_resources` /
`get_system_status` / `list_incidents`) and summarizes. Nothing is charged.

**What just happened:** the exact same agent loop as Part 1 — read → reason →
answer — but the "tools" now reach three facilities' live status APIs. You're
looking at three machine rooms from one editor. Notice the agent picks the right
server per system without you naming it.

## Step 3 — Find your allocation on each facility

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
> your `OLCF_IRI_TOKEN` was issued **without the compute scope** — re-mint it from
> myOLCF with compute enabled (see [PREREQUISITES.md](../PREREQUISITES.md#olcf--frontier--a-manually-issued-api-token)).

## Step 4 — Look around your filesystems

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
facilities. In Lab 09 you'll *move* data; today you're just reading.

---

## ✅ Checkpoint

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
