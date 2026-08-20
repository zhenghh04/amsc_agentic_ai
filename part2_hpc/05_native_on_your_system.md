# Lab 05 — Run Claude Natively on Your System (+ a First Job)

> **Part 2 · Running Claude on HPC Systems · ~35–50 min · Cost: ~1 node-minute
> (debug queue)**
>
> Prereq: [Lab 00](../part1_fundamentals/00_setup_claude_mag.md) (you know
> the MAG `settings.json` shape). Needs an **interactive account** on **one** of
> Polaris, Perlmutter, or Frontier — no MCP server, no IRI, nothing from
> [PREREQUISITES.md](../PREREQUISITES.md).

Every lab so far ran the agent **on your laptop**. This lab puts it **on the HPC
system itself** — `claude` runs as a process on a login node, editing files that
already live on the system's filesystem, with no staging step — and then has the
agent write, submit, and monitor a real scheduler job using the scheduler's own
commands.

Pick **one** system for this lab. Each step shows the per-system difference.

---

## Objectives

1. Install the Claude Code CLI on your system's login node and point it at MAG —
   **directly, with no tunnel** (MAG is public).
2. (Optional) Wrap the session in VS Code Remote-SSH for a full editor.
3. Have the agent run the **Part 1 simulation** as a real scheduler job, using
   `qsub`/`qstat` (Polaris) or `sbatch`/`squeue` (Perlmutter/Frontier).
4. Retrieve and read the output — and know what's structurally different from
   Part 3's IRI approach.

## Why no proxy? (the MAG payoff)

Some facilities' internal model gateways are intranet-only, so running an agent on
a login node needs an SSH tunnel just to reach them. **MAG is different** — it's a
public-cloud endpoint (`i2-api.genesis.american-science-cloud.org`), so a login
node with normal outbound internet reaches it directly. No SOCKS bridge, no `hpts`,
no second SSH hop. If (and only if) your login node blocks outbound HTTPS, add the
facility's HTTP proxy to the `env` block, or use Part 3 instead.

## Step 1 — SSH to your system

```bash
ssh <you>@polaris.alcf.anl.gov      # Polaris (ALCF)
ssh <you>@perlmutter.nersc.gov      # Perlmutter (NERSC)
ssh <you>@frontier.olcf.ornl.gov    # Frontier (OLCF)
```

## Step 2 — Install Node.js + the Claude Code CLI (user-local)

You don't have root on a shared login node, so install user-local — exactly as
[Lab 00](../part1_fundamentals/00_setup_claude_mag.md) recommends for any
shared machine:

```bash
node --version   # need 18+; if missing or old:
# via the module system, if one provides node (varies by system), or via nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# nvm isn't on your PATH yet — reopen your shell, or load it in the current one:
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                    # loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # loads nvm bash_completion
nvm install --lts

# Claude Code to a user prefix (never sudo, never global on shared infra)
npm install -g --prefix ~/.npm-global @anthropic-ai/claude-code
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
claude --version
```

## Step 3 — Point Claude Code at MAG (same as Lab 00 — no proxy)

On the login node, `~/.claude/settings.json` — identical to
[Lab 00 Step 3](../part1_fundamentals/00_setup_claude_mag.md#step-3--point-claude-code-at-mag):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://i2-api.genesis.american-science-cloud.org",
    "ANTHROPIC_AUTH_TOKEN": "<your-MAG-PAT>",
    "ANTHROPIC_MODEL": "claude-sonnet-4-6"
  }
}
```

Run `claude` and verify a reply:

> Say hello in one sentence and tell me which host you're running on.

**What just happened:** `claude` is now a process on the login node, editing files
on the system's own filesystem with no staging step — and its network traffic goes
straight to MAG, no tunnel. Contrast with an intranet gateway, which would need
the SSH-tunnel dance; MAG being public removes that entire lab.

> **(Optional) VS Code Remote-SSH.** Install the "Remote - SSH" extension
> (Microsoft), add a `Host` entry for your system in `~/.ssh/config`, connect,
> then install the **Claude Code** extension **on the remote** ("Install in SSH:
> …"). You get file-tree browsing and inline diffs against the system's
> filesystem. The MAG `settings.json` above (in the system's home dir) is shared
> regardless of how you connect.

---

## Section B — Run the simulation natively

Now have the agent run the **Part 1 heat-diffusion simulation** (or your own) as a
real scheduler job. First tell it your **project/account** — unlike Part 3, there's
no `get_project_allocations` tool here; look it up at the facility portal and give
it to the agent directly.

### Step 4 — Brief the run

> Write and submit a short job on **<system>** that runs a 1-D heat-diffusion
> simulation (like the one from Part 1) on one node and saves the output plot.
> Also print the hostname, the date, and the GPU info. Use the **debug** queue,
> **1 node**, **5-minute** walltime, and charge it to project **`<your-project>`**.
> Show me the script before you submit.

### Step 5 — Review the script (this is where systems differ)

The agent should produce a script matching your scheduler. **Polaris (PBS):**

```bash
#!/bin/bash -l
#PBS -A <your-project>
#PBS -N heat1d
#PBS -l select=1:system=polaris
#PBS -l walltime=00:05:00
#PBS -q debug
#PBS -l filesystems=home:eagle
#PBS -k doe
#PBS -o logs/
#PBS -e logs/

cd "$PBS_O_WORKDIR"
mkdir -p logs
hostname; date
nvidia-smi --query-gpu=name,memory.total --format=csv
module use /soft/modulefiles; module load conda; conda activate base
python heat1d.py
```

**Perlmutter (Slurm):**

```bash
#!/bin/bash
#SBATCH -A <your-account>
#SBATCH -J heat1d
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -N 1
#SBATCH --gpus-per-node=4
#SBATCH -t 00:05:00
#SBATCH -o logs/%x-%j.out

mkdir -p logs
hostname; date
nvidia-smi --query-gpu=name,memory.total --format=csv
module load pytorch          # or your own conda env
python heat1d.py
```

**Frontier (Slurm, AMD/ROCm):**

```bash
#!/bin/bash
#SBATCH -A <your-project>
#SBATCH -J heat1d
#SBATCH -p batch
#SBATCH -q debug
#SBATCH -N 1
#SBATCH -t 00:05:00
#SBATCH -o logs/%x-%j.out

mkdir -p logs
hostname; date
rocm-smi --showproductname          # AMD MI250X — NOT nvidia-smi
module load PrgEnv-amd rocm miniforge3
python heat1d.py
```

> **Per-system gotchas the agent must respect:**
> - **Polaris:** `-A`, `walltime`, and `filesystems` are all mandatory; use
>   `select=1:system=polaris`. Debug queue: one job per user.
> - **Perlmutter:** GPU nodes require `-C gpu`. Without it the job lands on CPU
>   nodes and `nvidia-smi` fails.
> - **Frontier:** GPUs are **AMD** — `rocm-smi`, not `nvidia-smi`, and a **ROCm**
>   PyTorch build. `debug` is a **QOS** (`-q debug`), used with `-p batch`.

### Step 6 — Submit, monitor, retrieve

> Looks right — submit it, then watch it until it's no longer queued or running,
> checking on a sensible cadence rather than hammering the scheduler.

The agent submits and polls with the *native* command (a `Bash` tool call, not an
MCP tool):

```bash
qsub run.sh   ;  qstat -u "$USER"        # Polaris
sbatch run.sh ;  squeue -u "$USER"       # Perlmutter / Frontier
```

Then retrieve:

> The job finished — show me stdout/stderr, confirm the GPU line, and open the
> plot the simulation produced.

**What just happened:** the same **stage → submit → monitor → retrieve** loop as
Part 3, but the agent drives real CLI commands with `Bash` rather than a
purpose-built tool. Nothing stops it from also running `qdel`/`scancel` — there's
no tool boundary here at all, which is exactly Part 2's trade-off.

### When it fails

Reading a failed log is the same loop as Lab 03 — point the agent at the log:

> Read `<the log path>` and tell me what failed, with quoted evidence and a fix.

The GPU-vs-host-OOM and walltime-timeout signatures from
[Lab 02](../part1_fundamentals/03_local_training.md) are exactly what these native jobs
produce.

---

## What's structurally different from Part 3

| | Part 2 (this lab) | Part 3 ([Lab 08](../part3_iri/08_iri_job_submission.md)) |
| --- | --- | --- |
| Submit | `qsub`/`sbatch` (shell) | `submit_job(...)` (named tool call) |
| Monitor | `qstat`/`squeue` (shell) | `get_job_status(...)` (named tool call) |
| Look up your project | portal / `sbank`, by hand | `list_projects()` / `get_project_allocations()` |
| What the agent *could* also do | Anything a shell can do on the login node | Only what the bundled server's tool list defines |

Neither is "more correct" — they're different trust boundaries. Part 2 gives the
agent a general-purpose shell on shared infrastructure; Part 3 gives it a fixed,
auditable set of named operations across all three facilities.

---

## ✅ Checkpoint

- [ ] `claude --version` works on your login node and it replied via MAG **with no
      tunnel**.
- [ ] The agent wrote a scheduler script correct for your system (PBS vs Slurm,
      `-C gpu` / `system=polaris` / `rocm-smi` as appropriate).
- [ ] `qsub`/`sbatch` returned a job ID and the agent polled to a terminal state
      without you refreshing it.
- [ ] You read the output, confirmed the GPU line, and opened the simulation's plot.

🎉 You can run `claude` directly on a real DOE system and drive a job with nothing
but a shell. Next: scale the training spine.

Continue to [Lab 06 — Scale the spine](06_scale_the_spine.md).

---

## Exercises

1. **Deliberate failure.** Ask for a script missing the account flag (or, on
   Polaris, missing the mandatory `-l filesystems=...`) on purpose, submit it, and
   let the agent diagnose the rejection from the scheduler's error text.
2. **Compare blast radius.** Ask the agent to run something *unrelated* to the job
   — "what's using the most disk in my home directory?" It just does it, no tool
   boundary. Now picture the same ask in Part 3: the one thing that would stop it
   is "no matching tool."
3. **Two nodes.** Rerun with 2 nodes (`select=2` / `-N 2`) and an MPI or `srun`
   launch. What did the agent change? Same shape as Lab 06's scaling.

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
