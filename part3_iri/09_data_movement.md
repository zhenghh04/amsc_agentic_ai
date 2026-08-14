# Lab 09 — Move Data with Globus

> **Part 3 · Orchestrating Job Submission via IRI · ~25–35 min · Cost: free (data transfer only)**
>
> Prereq: [Lab 08](08_iri_job_submission.md). Helpful: a small input file you can
> transfer, and (to move data to/from your laptop) a Globus Connect Personal
> endpoint — otherwise move data *between* facility paths.

Real jobs need inputs and produce outputs. Across DOE systems you move both with
**Globus** — reliable, restartable, parallel transfers between endpoints. This lab
has the agent stage data in, pull results out, and (the multi-facility payoff) move
data *between* facilities — all conversationally. One Globus Transfer token
(from [PREREQUISITES.md](../PREREQUISITES.md)) works for every facility's DTN.

---

## Objectives

1. Understand Globus endpoints and how the agent addresses each facility's storage.
2. Transfer a file **to** a facility filesystem and verify it landed.
3. Pull a result **back**, and move data **between two facilities**.
4. Monitor a transfer to completion (transfers are async, like jobs).

## Concepts (30 seconds)

- A **Globus endpoint** is a named data source/sink — a facility data-transfer
  node (DTN), or a Globus Connect Personal endpoint on your laptop.
- A transfer moves files **between two endpoints** by path. It runs in the
  background; you poll it for status — just like a job.
- **Per-facility endpoints and paths:**

| Facility | Common endpoints / roots | Notes |
| --- | --- | --- |
| **Polaris (ALCF)** | `home` (`/<you>`), `eagle` (`/eagle/<project>/…`) | IRI *also* has a filesystem API |
| **Perlmutter (NERSC)** | NERSC DTN → `/pscratch/sd/…`, `/global/homes/…`, `/global/cfs/cdirs/…` | |
| **Frontier (OLCF)** | OLCF DTN → `/ccs/home/…`, Orion scratch | **Globus is the *only* way** — no filesystem API on the IRI enclave |

- Put datasets and job outputs on **scratch/project** space, not home (home is
  small and often not mounted on compute).

## Step 1 — See the endpoints and paths

> What Globus endpoints and project-space paths can I use for the facilities I'm
> set up for? List what's currently in my scratch/project space on each.

The agent names the facility endpoints (its `globus_ls` tool documents the common
shorthands) and lists your directories with `globus_ls`.

> **Path form matters.** Globus addresses storage by its storage-root path. If a
> transfer path is rejected, ask the agent to confirm the correct root for that
> endpoint.

## Step 2 — Stage data in

Pick a small file (or have the agent create one), then:

> Transfer `<local-or-source path>` to my project space on **<facility>** at
> `<dest path>`, and give me the transfer task ID.

The agent starts a Globus transfer (`globus_transfer`) and returns a **task ID**.
Transfers are async — starting one doesn't mean it's done.

**What just happened:** the agent kicked off a background data movement. Note the
parallel with jobs: submit → get an ID → monitor. Same shape, different verb.

## Step 3 — Monitor and verify

> Monitor Globus task `<task-id>` and tell me when it's SUCCEEDED or FAILED.

Let it poll (`globus_transfer_status`). Then confirm it actually landed:

> List the destination directory and confirm the file is there with the right size.

**What just happened:** you verified the data arrived intact — not just that the
transfer was accepted. On a real run, "did my input arrive?" is worth answering
before you submit a job that depends on it.

## Step 4 — Pull a result back, and move between facilities

Use an output from Lab 08 (or make a small file), then:

> Transfer `<facility path>/<result>` back to `<local path>` and let me know when
> it's done.

(To reach your laptop you need a Globus Connect Personal endpoint; if you don't
have one, transfer between two facility paths instead — identical workflow.)

Then the multi-facility move (if you have two facilities):

> Now copy that same file from **<facility A>** directly to my scratch space on
> **<facility B>**. Give me the task ID and monitor it.

**What just happened:** you closed the data loop — in, out, and *across*. Globus
moved bytes directly between two DOE DTNs without routing through your laptop.
Combined with Lab 08's compute loop, you now have every half of a real
cross-facility run: **move data in → run job → move results out (anywhere).**

---

## ✅ Checkpoint

- [ ] You listed your endpoints and project-space paths.
- [ ] A transfer **to** a facility reached SUCCEEDED and you verified the file.
- [ ] A transfer **back** (to your laptop or another facility path) completed.
- [ ] (If multi-facility) you moved a file **directly between two facilities**.
- [ ] You monitored at least one transfer to a terminal state via its task ID.

You can now feed and drain a real workflow across facilities. Time for the capstone.

Continue to [Lab 10 — Spine end-to-end across facilities](10_end_to_end_across_facilities.md).

---

## Exercises

1. **A directory, recursively.** Ask the agent to transfer a small folder (not
   just a file) and note that recursive transfers are a flag it sets.
2. **Restart resilience.** Ask what happens if a transfer is interrupted — Globus
   restarts/space-checks are why it's preferred over `scp` for large data. One
   line.
3. **Right filesystem.** Ask why datasets and job outputs belong on scratch/project
   rather than home on each facility. Getting this right avoids quota grief later.
