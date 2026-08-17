# Lab 02 — MCP & Tools: How a Prompt Becomes a Tool Call

> **Part 1 · Fundamentals · ~20–30 min · No HPC allocation required**
>
> Prereq: [Lab 00](00_setup_vscode_claude_mag.md). Best after
> [Lab 01](01_hpc_simulation.md), so you've *seen* tool calls before we name them.

You've already made the agent act: in Lab 01 it wrote `heat1d.py`, ran it, and
saved a plot. Each of those was a **tool call**. This lab names the machinery —
tools, tool calls, and **MCP** — and has you add a new tool server yourself.
Understanding this is what lets you later connect the agent to *external*
services, including Polaris, Perlmutter, and Frontier (Part 3).

---

## Objectives

1. Explain the anatomy of a tool call: name + arguments → result → next step.
2. Distinguish **built-in tools** from **MCP servers**.
3. Add a public MCP server to Claude Code and use its tools.
4. Understand why MCP is the door to running real HPC work later.

## Anatomy of a tool call

When you asked the agent to run the simulation, under the hood a loop like this
ran:

```text
you: "write and run a 1-D heat diffusion sim"
      │
agent decides: I need to create a file
      │
      ▼   tool call
   { "tool": "Write", "arguments": { "path": "heat1d.py", "content": "..." } }
      │
      ▼
   tool runs → file is written
      │
agent decides: now run it  →  { "tool": "Bash", "arguments": { "command": "python heat1d.py" } }
      │
      ▼
   tool runs → returns stdout (the numbers)
      │
agent reads the result → decides next step (plot, or fix a bug) → maybe another tool call
      │
      ▼
   … repeats until the task is done → final answer to you
```

Two things to notice:

- **The model doesn't touch your files or run programs directly.** It *emits a
  request* to call a named tool with structured arguments; the harness runs the
  tool and hands back the result. The model only ever sees text going in and out.
- **It's a loop.** Write → run → read → reason → repeat. That loop is the whole
  definition of "agent."

## Built-in tools vs MCP servers

| | Built-in tools | MCP servers |
| --- | --- | --- |
| Examples | read/write files, run shell commands, edit code | a database, a web API, Globus, a scheduler, your app |
| Ship with | Claude Code itself | separate programs you connect |
| How added | already there | you register them (this lab) |
| Protocol | internal | **MCP** — an open standard |

**MCP (Model Context Protocol)** is a standard way to expose "here are my tools,
here's how to call them, here's what they return" to *any* agent. Because it's a
standard, a tool server written once works with Claude Code, other editors, or
custom agents. This is the key idea: **capability lives in MCP servers at the
edges; the agent just discovers and calls them.**

See what's connected right now — inside `claude`, run:

```text
/mcp
```

On a fresh setup you'll likely see none. Let's add one.

## Step 1 — Add a public MCP server

We'll add the official **filesystem** server. It's public, needs no secrets, and
exposes file tools scoped to a folder you choose. From a terminal:

```bash
claude mcp add fs -- npx -y @modelcontextprotocol/server-filesystem ~/agent-labs
```

- `fs` — the name you'll see in `/mcp`.
- everything after `--` is the command that launches the server.
- `~/agent-labs` — the one directory this server is allowed to touch.

List and confirm:

```bash
claude mcp list
```

> **The file approach (equivalent).** Instead of the CLI you can drop a
> `.mcp.json` in your working folder:
>
> ```json
> {
>   "mcpServers": {
>     "fs": {
>       "command": "npx",
>       "args": ["-y", "@modelcontextprotocol/server-filesystem",
>                "/absolute/path/to/agent-labs"]
>     }
>   }
> }
> ```
>
> Same result — Claude Code launches the server and imports its tools. This is
> exactly how the three facility servers are wired in Part 3's `.mcp.json`.
> Secrets (API keys, tokens) go in environment variables referenced by the
> config, never hard-coded here.

Restart `claude`, then run `/mcp` again — you should now see **fs** with its
tools listed.

## Step 2 — Use the new tools

Ask the agent to do something only the `fs` server is scoped for:

> Using the fs tools, list everything in my agent-labs folder and tell me the
> total size.

Watch the transcript: the tool calls now carry the `fs` server's tool names.

**What just happened:** you extended the agent's capabilities *without changing
the agent*. You registered a server; its tools appeared; the agent used them. Add
a different server and the agent can suddenly query a database, hit a web API, or
drive a cluster — same mechanism every time.

## Step 3 — See the boundary

Ask for something outside the server's scope:

> Using the fs tools, read /etc/hosts.

The server refuses — it's locked to `~/agent-labs`. **MCP servers define their
own boundaries.** This is central to trust: a tool can only do what its server
permits, no matter what the model "wants." When you later connect a facility
server, *it* decides what operations exist (and your credentials decide what
you're allowed to touch).

---

## ✅ Checkpoint

- [ ] You can explain a tool call as *name + arguments → result → next step*.
- [ ] `/mcp` shows the `fs` server and its tools.
- [ ] The agent used `fs` tools to inspect `~/agent-labs`.
- [ ] You saw the server refuse an out-of-scope path.

---

## Exercises

1. **Remove it.** `claude mcp remove fs`, restart, and confirm with `/mcp` that
   the tools are gone. You now control the agent's capability surface.
2. **Scope matters.** Re-add `fs` pointed at a *different* folder and confirm the
   agent's reach changed accordingly.
3. **Read a real schema.** Run `/mcp`, pick the `fs` server, and look at one
   tool's description and arguments. That description is exactly what the model
   reads to decide how to call it — which is why a facility server's tool
   descriptions (Part 3) have to be precise.

---

## Why this matters for HPC

Everything you did to run a simulation on your laptop scales up through the same
door: to make the agent submit to **Polaris**, **Perlmutter**, or **Frontier**,
move data with **Globus**, or monitor a training run, you connect it to a
**facility-provided MCP server** that wraps those APIs — then ask in plain
English, exactly as you did with `fs`. The agent loop doesn't change; only the
tools at the edge do.

That's Part 3 — see [part3_iri/README.md](../part3_iri/README.md) and
[PREREQUISITES.md](../PREREQUISITES.md) for the three bundled facility servers.
First, finish the spine: [Lab 03 — training](03_training.md) and
[Lab 04 — inference](04_inference.md). Or head back to the
[track overview](../README.md).

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
