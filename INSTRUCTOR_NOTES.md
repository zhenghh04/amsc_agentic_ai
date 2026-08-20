# Instructor Notes

For running the fundamentals track as a workshop (a ~half-day session works
well). Everything is self-contained; participants need only a laptop and a MAG
Personal Access Token.

## Timing (half-day, ~3.5 h with breaks)

| Block | Content | Time |
| --- | --- | --- |
| Intro | What is an agent? The read→act loop. The spine (sim/train/infer). Live demo of Lab 01. | 20 min |
| Lab 00 | Setup + MAG (do this together; it's the biggest failure point). | 40 min |
| Lab 01 | Drive a small simulation. | 40 min |
| Break | | 10 min |
| Lab 02 | MCP & tools. | 30 min |
| Lab 03 | Drive a small training run. | 40 min |
| Lab 04 | Drive an inference run. | 35 min |
| Wrap | "Going further" to HPC; the spine scaled up in Parts 2/3; Q&A. | 25 min |

The **spine** (Labs 01, 03, 04) is the heart of the workshop — the same three
workloads participants will scale up in Parts 2 and 3. Lab 02 explains the tool
machinery behind all of them and can run as a live demo if time is short.

- **Short (half-day):** Labs 00, 01 hands-on; Lab 02 live demo; Lab 03 hands-on;
  Lab 04 as a demo.
- **Full day:** all five, plus a look ahead at Part 2 or Part 3 on a real system.

## Pre-flight checklist (send to participants beforehand)

- [ ] Laptop with rights to install software (or the no-admin path in Lab 00).
- [ ] (Optional) VS Code installed (<https://code.visualstudio.com/>) — only if
      using the editor integration in Lab 00 Appendix A; the labs run from the terminal.
- [ ] Node.js 18+ installed (`node --version`).
- [ ] A **MAG account** and a **Personal Access Token** generated at
      <https://portal-lite.genesis.american-science-cloud.org/> *before* the
      session (the PAT is shown once — have them save it in a password manager).
- [ ] Comfortable enough with a terminal to `cd`, edit a file, run a command.
- [ ] Python 3 available (for Lab 01's simulation and Lab 03's training).

> **Biggest risk: MAG access.** Have participants verify Lab 00 Step 4 (a
> round-trip reply) *before* the workshop, or arrive early. MAG is public-cloud,
> so there's no VPN/proxy to fight — the usual failure is a mistyped base URL or a
> PAT that was never copied. Backup: participants with a personal Anthropic key
> can use [Lab 00 Appendix B](part1_fundamentals/00_setup_claude_mag.md#appendix-b--the-non-mag-path).

## Answer key — what "success" looks like per lab

**Lab 00.** A reply to the Step 5 prompt confirming the MAG base URL and model.
The single most common failure is `settings.json` not being reloaded — remind
everyone to fully restart Claude Code.

**Lab 01 (simulation).** The agent should:
- write a small self-contained simulation (e.g. a 1-D heat/diffusion solver, an
  N-body or SIR ODE) and *run it*,
- produce a concrete artifact — a plot saved to a PNG and/or a printed final
  quantity,
- state the result with evidence (the number, the figure), not just "it worked",
- iterate at least once when you change a parameter.
Red flag: claiming success without showing the output → fix with a grounding
prompt.

**Lab 02 (MCP).** `/mcp` shows the `fs` server; the agent uses its tools on
`~/agent-labs`; the server refuses an out-of-scope path. Land the takeaway:
**capability is added at the edge via MCP; the agent loop never changes.**

**Lab 03 (training).** The agent writes a tiny training script (e.g. an MLP/CNN
on a small dataset), runs it, reads the loss/accuracy from the log, and iterates
(learning rate, batch size). If it hits an OOM, it should distinguish GPU OOM
(`torch.cuda.OutOfMemoryError`) from host OOM (`oom-kill`/137) — the sample logs
in `samples/` give you a failure to triage even without a GPU. Takeaway: the
**submit → read log → fix → resubmit** loop is the same one that drives real HPC.

**Lab 04 (inference).** The agent runs inference two ways — a call to MAG, and
(optionally) a tiny local model — and reports the output plus a rough
latency/throughput. Takeaway: serving is the same loop; on real systems it just
gets a GPU and a bigger model (Part 2/3).

## Teaching points worth stressing

- **Grounding and verification** are the durable skills — models change, these
  habits don't. Make participants *deliberately* trip the agent into a
  hallucination (Lab 01 Exercise 1) so they learn to demand evidence.
- **The spine is one story.** The sim/train/infer they run on a laptop today are
  the *same three* they'll scale to Polaris/Perlmutter/Frontier — nothing is a
  throwaway toy.
- **Descriptions are routing signals** — for MCP tools (Lab 02) especially.
  Precision there is why the agent picks the right capability.
- **The loop is the whole idea.** Once they see read→reason→act→observe→repeat,
  everything (including HPC across three facilities) is the same loop with
  different tools.

## Running Parts 2 and 3 (real jobs)

Parts 2 and 3 are two independent ways to reach the DOE systems
([part2_hpc/README.md](part2_hpc/README.md),
[part3_iri/README.md](part3_iri/README.md)) — run Part 3 as a workshop session;
treat Part 2 as a self-serve add-on.

**Part 3 (Labs 07–10, orchestrate via IRI)** is the one to schedule as a
**separate, hands-on session** with different logistics: every participant needs
an **account + allocation on at least one facility** and the bundled IRI MCP
servers authenticated ([PREREQUISITES.md](PREREQUISITES.md)) — sort this out
*well* before the session, as account/allocation approval takes time. It spends
real node-hours, so brief cost/etiquette up front (debug queue, 1 node, minutes).
The capstone (Lab 10) runs the Part 1 spine end-to-end and, for multi-facility
users, the *same* workload across all three systems — a memorable finish.

**Part 2 (Labs 05–06, native on a login node)** is **self-serve reference
material** — it needs an *interactive account* on one system, a heavier and less
uniformly available ask than Part 3's API access. Because MAG is public, there's
no proxy tunnel to set up (a real simplification over intranet-only gateways).
Point interested participants to it afterward unless most of the room already has
a login on one of the systems.

## After the workshop

- Invite participants to share how they adapted the spine to *their* science
  (their own simulation, their own model) — a small internal example library is a
  great outcome.
- Point interested users to [Part 2](part2_hpc/README.md) and
  [Part 3](part3_iri/README.md) (real jobs), [GOING_FURTHER.md](GOING_FURTHER.md),
  and their facility's user support.

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
