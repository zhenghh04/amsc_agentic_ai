# Part 1 — Fundamentals

Everything here runs with just **Claude Code + MAG** (VS Code optional). No special
repository, no HPC allocation, no queue. You'll get real, useful results — a
simulation you can plot, a model you can train, an inference you can call — and
learn the core ideas everything else builds on: **agents call tools**, and the
**submit → run → read → iterate loop** is the same at every scale.

| Lab | Title | Time | Needs |
| --- | --- | --- | --- |
| [00](00_setup_claude_mag.md) | Set up Claude Code and MAG | 15–25 min | A laptop, a MAG Personal Access Token |
| [01](01_local_simulation.md) | The 101: drive a small **local** simulation | 30–40 min | Lab 00 |
| [02](03_local_training.md) | Drive a small **local** training run | 30–40 min | Lab 01 |
| [03](04_local_inference.md) | Drive a small **local** inference run | 30–40 min | Lab 01 |

**Suggested order:** 00 → 01 → 02 → 03. Labs 01, 02, and 03 are the
**spine** — simulation, training, inference — the same three workloads you'll
scale up on real DOE systems in Parts 2 and 3.

## The mental model you'll leave with

```text
     you (plain English)
            │
            ▼
   ┌─────────────────┐     decides which tool,
   │   the agent     │────▶ with which arguments
   │  (Claude, via   │
   │   MAG gateway)  │◀──── reads the result, decides the next step
   └─────────────────┘
            │ tool call
            ▼
   ┌─────────────────┐
   │  tools it can    │  a shell, a file writer, a plotter,
   │  call            │  and — later — HPC facilities via MCP
   └─────────────────┘
```

An **agent** is an LLM in a loop that can *act* — it reads your request, calls a
tool, looks at the result, and decides what to do next, repeating until the task
is done. **MCP** (Model Context Protocol) is the open standard that lets the
agent discover and call those tools. The **spine** (simulation → training →
inference) is the throughline: you run tiny versions here and scale the *same
three* up in Parts 2 and 3.

Start with [Lab 00](00_setup_claude_mag.md).

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
