# Troubleshooting

Common snags, grouped by lab. Most issues are setup (Lab 00) or "the agent did
something unexpected" (grounding). If you're stuck longer than a few minutes,
skip ahead and come back — nothing here is a dead end.

## Lab 00 — Claude Code / MAG

**`claude: command not found`**
: The CLI didn't install or isn't on your `PATH`. Re-run
  `npm install -g @anthropic-ai/claude-code`. If `npm -g` is blocked, install to
  a user prefix (`npm install -g --prefix ~/.npm-global @anthropic-ai/claude-code`)
  and add `~/.npm-global/bin` to `PATH`. Confirm Node is 18+ with `node --version`.
  **No admin rights?** Install Node via a per-user manager (nvm / nvm-windows), or
  use the native installer (`curl -fsSL https://claude.ai/install.sh | bash`, or
  `irm https://claude.ai/install.ps1 | iex` on Windows) — it drops `claude` into
  your home directory, no admin needed.

**The VS Code extension doesn't pair with the CLI** (optional — see Lab 00 Appendix A)
: Open the integrated terminal and run `claude`, then `/ide` and select VS Code.
  Make sure the "Claude Code" extension (publisher Anthropic) is installed and
  enabled. VS Code is optional for this track — every lab works from the terminal.

**401 / 403 / "invalid api key" from MAG**
: Check `~/.claude/settings.json` (native Windows:
  `%USERPROFILE%\.claude\settings.json`): `ANTHROPIC_BASE_URL` must be
  `https://i2-api.genesis.american-science-cloud.org` and `ANTHROPIC_AUTH_TOKEN`
  must be your MAG **Personal Access Token** (PAT), not your username. Restart
  Claude Code after any edit — settings are read at startup. Still 401? Your PAT
  may have expired or been revoked — mint a fresh one at
  <https://portal-lite.genesis.american-science-cloud.org/> (MAG shows the full
  key only once; copy it immediately).

**"model not found" / unsupported model**
: The `ANTHROPIC_MODEL` value isn't served by MAG. Use an alias
  (`claude-sonnet`, `claude-opus`, `claude-haiku`) to auto-track the newest
  version, or a pinned string MAG lists (`claude-sonnet-4-6`, `claude-opus-4-6`,
  `claude-haiku-4-5`).

**"quota exceeded" / your MAG project is out of budget**
: MAG PATs are scoped to an approved AmSC Genesis Mission RFA project with its own
  budget. If a project is exhausted, generate a PAT under a different approved
  project in the portal, or ask your project lead about the budget.

**Edits to `settings.json` seem ignored**
: You must fully quit and relaunch the `claude` process. The base URL and model
  are read once at startup.

## Lab 01 — Local simulation

**The agent writes code that won't run (missing numpy/matplotlib)**
: Ask it to use only the Python standard library, or to `pip install` what it
  needs into a virtual environment first. On a laptop, `python3 -m venv .venv &&
  source .venv/bin/activate && pip install numpy matplotlib` once is simplest.

**It claims the simulation "converged" without showing evidence**
: Your prompt wasn't grounded. Add: *"show me the actual output/plot and the
  numeric result; don't assert success without evidence."* Then look at the plot
  or the final numbers yourself.

**The plot never appears**
: Headless matplotlib needs a file backend — ask the agent to `savefig(...)` to a
  PNG rather than `show()`, then open the PNG.

## Lab 02 — MCP & tools

**`/mcp` shows nothing after adding a server**
: Restart `claude`. Confirm the server is registered with `claude mcp list`.
  Ensure the launch command works on its own (e.g. `npx -y
  @modelcontextprotocol/server-filesystem ~/agent-labs` should start and wait).

**`npx` / server won't start**
: Node/npm missing or offline. `npx` downloads the server on first run, so the
  first launch needs network. Verify `node --version` and connectivity.

**The agent ignores the new tools**
: Ask it explicitly to *"use the fs tools to …"*. Then read the tool's
  description via `/mcp` — a vague description makes the model less likely to
  reach for it.

**A tool refuses an action**
: That's the server's boundary doing its job (e.g. filesystem server locked to
  one folder). Re-add the server with the scope you actually need.

## Lab 03 — Training

**GPU vs host out-of-memory**
: These look alike but are different. GPU OOM shows
  `torch.cuda.OutOfMemoryError` (device capacity) → reduce batch size, enable
  AMP/mixed precision, gradient accumulation, or
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. Host OOM shows
  `oom-kill` / exit code 137 (cgroup) → stream/shard the data, fewer dataloader
  workers, or a bigger-memory node. Ask the agent to quote the exact failing line
  before it proposes a fix.

**No GPU on the laptop**
: Expected — Part 1 training is tiny and runs on CPU. The *point* is the loop
  (write → run → read the loss → iterate), not the FLOPs. GPUs enter in Parts 2/3.

**Loss is NaN / not decreasing**
: Ask the agent to lower the learning rate, check data normalization, and print
  the loss every few steps. Treat it as a real debugging loop — that's the skill.

## Lab 04 — Inference

**MAG returns an error when the agent calls it as a tool**
: Two different uses of MAG can collide. Claude Code *itself* talks to MAG (your
  agent). If the lab's inference *task* also calls MAG, it needs its own PAT in
  the environment the script runs in — don't assume the script inherits Claude
  Code's. Set `AMSC_I2_API_KEY` in the shell the script uses.

**A local (non-MAG) model download is slow or fails**
: Small HF models still need network on first pull. Pick a genuinely tiny model
  for the laptop (e.g. a distilled or <1B model), or do the inference against MAG
  and defer local serving to Part 2/3 where GPUs exist.

## Lab 05 — Native on your system (Part 2)

**`claude` on the login node can't reach MAG**
: Unlike Argonne's internal Argo gateway, MAG is a **public-cloud** endpoint, so
  most login nodes reach it over normal outbound HTTPS with no tunnel. If your
  login node blocks outbound 443, set the facility's HTTP proxy in the `env`
  block (Polaris/Frontier compute-proxy hosts differ — check the system's docs)
  or fall back to Part 3 (agent on your laptop, facility via MCP).

**`npm install -g` fails with a permissions error on the login node**
: Same fix as Lab 00 — install to a user prefix:
  `npm install -g --prefix ~/.npm-global <package>`, and make sure
  `~/.npm-global/bin` is on `PATH` (`which claude`).

**`qsub`/`sbatch` rejects the script with a resource error**
: - **Polaris (PBS):** needs `-A` (account), `-l walltime`, `-l filesystems`,
    `-q debug`, and `-l select=1:system=polaris`.
  - **Perlmutter (Slurm):** GPU nodes need `-C gpu`; also `-A <account>`,
    `-q debug`, `-N 1`, `-t`, `--gpus-per-node=4`.
  - **Frontier (Slurm):** `-A <project>`, `-p batch` (add `-q debug` for the
    high-priority QOS), `-N 1`, `-t`; GPUs are AMD — use `rocm-smi`, not
    `nvidia-smi`.

**Job stays queued and a second submission is rejected**
: Debug queues cap concurrent jobs per user (often 1). Check `qstat -u $USER`
  (Polaris) or `squeue -u $USER` (Perlmutter/Frontier) for a lingering job before
  assuming the scheduler is stuck; delete it (`qdel`/`scancel`) if unneeded.

**Agent doesn't know the project/account name**
: Unlike Part 3, there's no `get_project_allocations` tool here. Look it up at
  the facility portal (or run `sbank`/`iris`/`myproject` if available) and give
  it to the agent directly.

## Lab 06 — Scale the spine (Part 2)

**The AMD/NVIDIA split**
: Perlmutter and Polaris are NVIDIA (CUDA PyTorch, `nvidia-smi`); Frontier is AMD
  (ROCm PyTorch, `rocm-smi`). If the agent installs a CUDA build on Frontier it
  will fail to see GPUs — tell it the target is MI250X / ROCm.

**Data-parallel launch differs by system**
: Polaris uses `mpiexec`; Perlmutter and Frontier use `srun`. Let the agent read
  the system's docs (or tell it) rather than copying a launch line from another
  machine.

## Lab 07 — Connect & explore (Part 3)

**`/mcp` doesn't show one of the servers**
: Most likely `claude` wasn't launched from inside `amsc_agentic_ai/` (that's
  where `.mcp.json` lives). A server that shows but says "not authenticated" just
  means you haven't set that facility's token — harmless if you don't use it.

**A read-only call returns 401**
: `list_resources`/`get_system_status` need no auth, but `list_projects` does.
  Run that facility's auth step in [PREREQUISITES.md](PREREQUISITES.md) Step 2.
  For OLCF, confirm your `OLCF_IRI_TOKEN` was issued **with the compute scope**.

## Lab 08 — IRI job submission (Part 3)

**Job dies immediately with exit 127 (command not found)**
: The script's `#!/bin/bash -l` login shell wasn't honored, so modules/conda were
  off PATH. The bundled servers force a login shell for `bash`/`sh` invocations;
  if you call the script directly, keep the `-l` shebang.

**Wrong account / queue burned allocation or landed in the wrong partition**
: Always have the agent read your account with `list_projects` /
  `get_project_allocations` first (Lab 07) and state queue/nodes/walltime/account
  before submitting. Never let it guess these.

## Lab 09 — Data movement (Part 3)

**Path form rejected**
: Globus addresses storage by its storage-root path (e.g. `/eagle/<project>/…`
  on ALCF, `/pscratch/sd/…` on NERSC, Orion scratch on OLCF). A compute-node job
  sees the mounted path. If a transfer path is rejected, ask the agent to try the
  other root for that endpoint.

**Reaching your laptop**
: You need a Globus Connect Personal endpoint on the laptop. No GCP? Transfer
  *between* two facility paths instead — the workflow is identical.

## Lab 10 — Spine across facilities (capstone)

**The same job works on one system but not another**
: That's the lesson, not a bug — schedulers, GPU vendors, and module stacks
  differ. Let the agent adapt per system (CUDA vs ROCm, `mpiexec` vs `srun`,
  `-C gpu` vs `select=...:system=polaris`). The *loop* is portable; the launch
  details are not.

## General

**The agent is non-deterministic**
: Two runs of the same prompt can differ. Judge by outcome, not by matching a
  transcript. If a result is wrong, refine the prompt (more grounding, clearer
  schema) rather than re-running blindly.

**It's doing too much / going off track**
: Interrupt, and give a narrower instruction. Short, specific asks beat one giant
  paragraph.

**Still stuck?**
: For editor/agent issues, the Claude Code docs. For MAG, the AmSC MAG docs
  (<https://amsc-docs-d762d2.gitlab.io/model-access-gateway>). For anything
  facility-specific, that facility's user support (see
  [PREREQUISITES.md](PREREQUISITES.md) Reference table).

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
