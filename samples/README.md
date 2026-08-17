# Sample logs

Synthetic HPC job logs for the training lab. They're fabricated for teaching
(fake job IDs, hostnames, paths) but mirror real failure signatures you'll meet
on DOE systems — one per facility. Use them if you don't have a failed log of
your own handy.

## Job failure logs — [Lab 03](../part1_fundamentals/03_training.md)

| File | System style | What fails | Root cause |
| --- | --- | --- | --- |
| [`polaris_train_ddp.o8123456`](polaris_train_ddp.o8123456) | ALCF Polaris (PBS, NVIDIA A100) | PyTorch DDP training | **GPU** out-of-memory (`torch.cuda.OutOfMemoryError`, A100 40 GB) |
| [`perlmutter_preprocess.out`](perlmutter_preprocess.out) | NERSC Perlmutter (Slurm) | Data preprocessing | **Host** RAM out-of-memory (cgroup `oom-kill`, exit 137) |
| [`frontier_train_timeout.out`](frontier_train_timeout.out) | OLCF Frontier (Slurm, AMD MI250X/ROCm) | LLM training | **Walltime timeout** (`CANCELLED ... DUE TO TIME LIMIT`), no checkpoint written |

Three distinct failure classes across the three facilities you'll use in Parts 2
and 3:

- **GPU OOM** vs **host OOM** look alike ("out of memory") but have different
  causes and fixes — the core distinction Lab 03 Step 4 teaches.
- The **Frontier timeout** is a *different category* entirely (the job never
  errored — it ran out of wall-clock before its first checkpoint), and it's on
  **AMD/ROCm** hardware (`rocm-smi`, not `nvidia-smi`) — good practice for the
  "third failure mode" exercise and for the cross-facility awareness Part 2/3
  needs.

Point the agent at any of them: *"read this log and tell me what failed, the root
cause with quoted evidence, and how to fix it."*

---

*Tutorial created by Huihuo Zheng, huihuo.zheng@anl.gov, Trinity Science.*
