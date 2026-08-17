# Lab 06 — Scale the Spine: a Real Training Run, Natively

> **Part 2 · Running Claude on HPC Systems · ~30–45 min · Cost: ~a few
> node-minutes (debug queue)**
>
> Prereq: [Lab 05](05_native_on_your_system.md) — `claude` replies on your login
> node and you've run one native job. Helpful:
> [Lab 03](../part1_fundamentals/03_training.md) (the laptop training run).

Lab 05 ran the *simulation* spine workload on a real node. This lab scales the
*training* workload — the CNN from [Lab 03](../part1_fundamentals/03_training.md) —
onto real GPUs, then to **data-parallel across all GPUs on a node**. Same loop,
same skills; the only new things are the GPU and the launcher.

Do this on the **one** system you set up in Lab 05.

---

## Objectives

1. Run the Part 1 training on **one real GPU** and confirm it uses the device.
2. Scale to **data-parallel across all GPUs** on one node (`mpiexec` on Polaris,
   `srun` on Perlmutter/Frontier).
3. Read the metrics, and use the failure-triage loop when scaling breaks something.
4. Feel the CUDA-vs-ROCm difference firsthand (Frontier is AMD).

## Step 1 — Train on one GPU

> Take the training script from Part 1 (the small CNN on MNIST) and run it here as
> a debug-queue job on **1 node using 1 GPU**, charged to **`<your-project>`**.
> Make sure it actually runs on the GPU — print the device and confirm it's not
> silently on CPU. Report the final test accuracy and the wall-clock time. Show me
> the script before submitting.

**What just happened:** the same training you ran on your laptop CPU now runs on a
datacenter GPU. The "confirm it's not silently on CPU" check matters — a CUDA
build on Frontier, or a missing `-C gpu` on Perlmutter, silently falls back to CPU
and you'd wonder why it's slow.

> **The AMD/NVIDIA split.** Polaris and Perlmutter are NVIDIA → CUDA PyTorch,
> `torch.cuda.is_available()`, `nvidia-smi`. **Frontier is AMD** → a **ROCm**
> PyTorch build, `rocm-smi`. Tell the agent the target so it installs/loads the
> right stack; a CUDA wheel on Frontier will not see the MI250X.

## Step 2 — Scale to all GPUs on the node (data-parallel)

> Now scale it to data-parallel training across **all GPUs on one node** — 4 on
> Polaris/Perlmutter, 8 GCDs on Frontier — using PyTorch DDP. Keep it in the debug
> queue, short walltime. Show me the launch command and the per-rank device
> assignment, then submit and report the accuracy and throughput vs the 1-GPU run.

The launcher differs by system — let the agent get this right (or tell it):

- **Polaris:** `mpiexec -n 4 -ppn 4 python train.py …` (PBS + HPE MPI).
- **Perlmutter:** `srun -n 4 --gpus-per-node=4 python train.py …` (Slurm).
- **Frontier:** `srun -n 8 --gpus-per-node=8 python train.py …` (Slurm; 8 GCDs).

**What just happened:** you scaled a workload from 1 device to a whole node by
*describing* it. The science (the model, the data) didn't change — only the launch
geometry did. That's the essence of "the spine scales": the same three workloads,
bigger.

## Step 3 — Read the scaling, honestly

> Compare the 1-GPU and full-node runs: accuracy, wall-clock, and
> images/second. Did throughput scale roughly with GPU count? If it scaled
> *less* than linearly, what are the likely reasons (data loading, small batch,
> communication overhead)? Don't claim a speedup you didn't measure.

**What just happened:** the "verify, don't trust — especially speedups" habit from
Part 1 now has real stakes. Near-linear scaling on a tiny model is unlikely
(overheads dominate); naming *why* is the analysis.

## Step 4 — When scaling breaks something

Scaling up trips new failures — an OOM at the bigger effective batch, a DDP init
hang, a walltime that was fine for 1 GPU but not the setup overhead of DDP. Point
the agent at the log:

> Read `<the job log>` and tell me what failed, with quoted evidence and a ranked
> fix. Distinguish a GPU OOM from a host OOM from a timeout.

This is the same triage from [Lab 03](../part1_fundamentals/03_training.md) —
the `samples/` logs (`polaris_train_ddp` GPU OOM, `perlmutter_preprocess` host OOM,
`frontier_train_timeout` walltime) are the exact shapes you'll now hit for real.
Fix and resubmit; loop until it succeeds.

---

## ✅ Checkpoint

- [ ] The 1-GPU run confirmed it used the GPU (not a silent CPU fallback) and
      reported accuracy + time.
- [ ] The full-node DDP run ran with the correct launcher for your system and
      reported accuracy + throughput.
- [ ] You compared throughput and reasoned about sub-linear scaling honestly.
- [ ] (If it failed) you triaged the log and resubmitted.

🎉 **You've completed Part 2.** You ran two spine workloads — simulation and
training — natively on a real DOE GPU system, driven by an agent with nothing but
a shell. Curious about doing the same across *all three* facilities from your
laptop, through a fixed, auditable tool set? See
[Part 3 — Orchestrating Job Submission via IRI](../part3_iri/README.md).

Back to the [Part 2 overview](README.md).

---

## Exercises

1. **Inference on the GPU.** Run the Part 1 inference workload here on one GPU and
   compare latency/throughput to your laptop CPU number — the measured speedup you
   couldn't claim in Lab 04.
2. **Serve it.** Ask the agent to stand up a tiny `vLLM` (or FastAPI) inference
   server on a compute node and send it a request. That's the serving pattern
   Part 3's capstone can also drive.
3. **Two nodes.** Push DDP to 2 nodes. What changed in the launch geometry and the
   scheduler request? Note how the *loop* stayed identical.

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
