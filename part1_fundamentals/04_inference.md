# Lab 04 — Drive an Inference Run

> **Part 1 · Fundamentals · ~30–40 min · No HPC allocation required**
>
> Prereq: [Lab 01](01_hpc_simulation.md). Helpful:
> [Lab 03](03_training.md) (the training half of the ML story).

The last workload of the spine is **inference** — using a trained model to make
predictions, and measuring how fast. You'll run inference two ways: as a **call to
MAG** (a hosted large model), and as a **small local model** on your laptop. In
Part 2/3 the local path scales onto a GPU node with a real serving stack (vLLM),
but the loop is identical.

> Two flavors of "inference" show up in practice, and this lab touches both:
> **(a)** calling a hosted LLM through MAG (no GPU, no model to manage), and
> **(b)** running your *own* model locally (the classifier you trained in Lab 03,
> or a small downloaded model). Do (a) for sure; do (b) if you have the packages.

---

## Objectives

1. Run **hosted inference** through MAG from a script (not just the Claude Code
   chat) and read the response.
2. Run **local inference** with a small model and measure **latency/throughput**.
3. Understand the difference between the agent *using* MAG and your *task* using
   a model — and why serving is the same submit → run → read loop.
4. Know exactly what changes when this moves to a GPU node (Part 2/3).

---

## Concepts (30 seconds)

- **Inference** = a forward pass through a trained model: text in → text out for
  an LLM, image in → label out for the Lab 03 classifier.
- **Two roles for MAG.** Claude Code (the *agent*) already talks to MAG — that's
  how it thinks. A *task* you write can *also* call MAG as a plain HTTP endpoint.
  Those are independent: the task needs its own token in its own environment.
- **What matters at scale:** latency (time per request) and throughput (requests
  or tokens per second). Those numbers are the whole reason inference gets a GPU.

## Step 1 — Hosted inference through MAG

Have the agent write a tiny client that calls MAG directly (the same endpoint
Claude Code uses), so you see inference as a *program*, not a chat:

> Write a small Python script `mag_infer.py` that sends one chat completion
> request to the MAG endpoint (`https://i2-api.genesis.american-science-cloud.org`,
> Anthropic Messages API) using my PAT from the `AMSC_I2_API_KEY` environment
> variable, model `claude-haiku-4-5`. Prompt it to classify the sentiment of three
> example sentences. Print the model's answer and the wall-clock time for the
> request. Then run it.

Before it runs, export your PAT in the shell the script will use:

```bash
export AMSC_I2_API_KEY=<your-MAG-PAT>
```

**What just happened:** you called a frontier model as an *API*, from your own
code — the same gateway the agent uses, but now under your program's control. Note
the token plumbing: Claude Code's PAT and your script's PAT are separate; the
script only sees what's in its environment.

> Use a cheap alias like `claude-haiku` for throwaway inference so you don't spend
> your project's budget on a sentiment demo.

## Step 2 — Local inference with your own model

Point inference at a model *you* control — the classifier from
[Lab 03](03_training.md) is perfect:

> Load the model I trained in Lab 03 (`train.py` / its saved checkpoint) and run
> inference on 100 test images. Report the accuracy, the average per-image latency
> in milliseconds, and the throughput in images/second. Save the numbers to
> `infer_metrics.json` and show me the real measurements.

No Lab 03 checkpoint handy? Ask for a tiny downloaded model instead:

> Alternatively, download a very small text model from Hugging Face (well under
> 1B params so it runs on CPU), run inference on a few prompts, and report latency
> and tokens/second.

**What just happened:** you ran the *serving* half of ML — take a fixed model,
feed it inputs, measure speed. On a laptop CPU the throughput is modest; that
modest number is exactly the motivation for a GPU.

## Step 3 — Read the performance, and project it to a GPU

> From the latency/throughput you just measured on CPU: roughly what would change
> if this ran on one GPU (an A100 on Polaris/Perlmutter, or an MI250X GCD on
> Frontier)? What batch size would improve throughput, and where's the tradeoff
> with latency? Don't overclaim a speedup — reason about it and say what you'd
> have to measure to know.

**What just happened:** you connected a laptop measurement to the reason HPC
exists. The agent should talk about batching, memory-bound vs compute-bound, and
the need to *measure* rather than assume — the same "verify, don't trust" habit,
applied to performance.

> **Verify, don't trust — especially speedups.** A claimed "10x on GPU" means
> nothing without a measured run. In Part 2/3 you'll actually run it on the GPU
> and check.

---

## ✅ Checkpoint

- [ ] `mag_infer.py` ran and returned a real model response with a timing.
- [ ] You ran local inference and have measured latency + throughput in
      `infer_metrics.json` (from your Lab 03 model or a small downloaded one).
- [ ] You can explain the two roles of MAG (agent vs task) and why the task needs
      its own token.
- [ ] The agent projected to a GPU *without* overclaiming an unmeasured speedup.

🎉 **You've completed the spine on a laptop:** simulation (Lab 01), training
(Lab 03), and inference (Lab 04) — plus the tool machinery underneath (Lab 02).

---

## Exercises

1. **Batch it.** Re-run local inference with batch sizes 1, 8, 32 and plot
   throughput vs batch size. Notice throughput rises while per-request latency
   grows — the core serving tradeoff.
2. **Two models, one task.** Send the same prompt to a MAG `claude-haiku` and a
   `claude-sonnet` alias; compare answer quality and latency. Picking the right
   model for the job is a real deployment decision.
3. **Prep for vLLM.** Ask the agent: *"what is vLLM, and why would I use it to
   serve an LLM on a GPU node instead of a plain PyTorch loop?"* You'll stand one
   up for real in Part 2/3.

---

## Where this points

Inference on a laptop is the same loop you'll run on a GPU node: load a model,
feed inputs, measure speed. In Part 2 you run it natively on a compute node; in
Part 3 the agent submits a serving job and sends it requests — the throughput just
gets a lot bigger. That's the whole spine (sim → train → infer) ready to scale.

**Back to the [track overview](../README.md).** Part 1 complete. Next: put the
agent on a real system — [Part 2](../part2_hpc/README.md) (native on a login
node) or [Part 3](../part3_iri/README.md) (orchestrate all three facilities from
your laptop).

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
