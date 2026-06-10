# Goal Template — Improve TSP Upper Bound

Use this prompt with `/goal` from the TSP repo root.

```txt
/goal
Project: /home/werserk/3-education/hse/combinatorial-optimization/tsp

Primary objective:
Improve the verified upper bound for the 1114-city TSP challenge instance and reduce the current optimality gap by finding a shorter valid tour.

Current best:
- upper_bound = 73934
- upper_artifact = results/best/step6-lkh-best.json
- lower_bound = 65493.4373688764
- lower_artifact = results/best/step9-held-karp-one-tree.json
- current interval = 65493.4373688764 <= OPT <= 73934
- current gap to lower = 12.887646411936071%

Success condition:
Produce a valid tour with independently verified length strictly less than 73934, with a new best artifact under results/best/ and an updated gap calculation.

This is not a research-only goal. Research is required, but success requires metric improvement. If no improvement is found, stop only with an evidence-based exhaustion report.

Required skills and playbooks:
- Use skill: research-to-experiment-cycle.
- Follow docs/playbooks/tsp-upper-bound-improvement.md.
- Follow docs/playbooks/tsp-experiment-protocol.md.
- Apply docs/playbooks/tsp-result-review-gate.md before promoting any result.

Allowed methods:
- web research over papers, solver docs, GitHub, and benchmark reports;
- local open-source solver builds;
- LKH portfolios and targeted longer waves;
- Concorde/EAX/Lin-Kernighan variants or other relevant local solver attempts;
- improvements to our post-optimization heuristics;
- multi-hour local runs.

Compute policy:
Aggressive local. Hours are acceptable; days, paid cloud, remote compute, destructive system-wide installs, or external submissions require user approval.

Required cycle per serious attempt:
1. Research sources and prior project artifacts.
2. Rank candidate methods/configs by expected UB impact, feasibility, cost, and integration risk.
3. Select the next candidate.
4. Define the tour-validity and independent-verification contract before claiming any upper bound.
5. Implement or integrate with tests/verifiers.
6. Run bounded experiments with logs/artifacts.
7. Independently verify the candidate tour against data/raw/matrices/M.txt.
8. Promote only strict verified improvements; otherwise write a negative result note.

Priority tracks:
1. Stronger LKH portfolio and targeted longer waves.
2. Alternative external solvers/metaheuristics, especially EAX/LK variants and Concorde as reference.
3. Own post-optimization around the current best tour.
4. Hybrid UB/LB-informed candidate sets if lower-bound work exposes useful structure.

Parallel coordination:
This goal may run alongside a lower-bound improvement goal. Before final gap reporting, reload the current best lower-bound artifact from disk. Do not overwrite another process's best artifact unless this run has a strict verified improvement and passes the review gate.

Stop conditions:
- verified UB improves below 73934;
- three serious upper-bound tracks are exhausted with documented evidence;
- the next run exceeds aggressive-local compute budget;
- explicit user approval is needed;
- the selected approach produces invalid or unverifiable tours.

Deliverables on success:
- results/best/stepXX-<method>-upper-bound.json
- notes/stepXX-<method>-upper-bound.md or next numbered note
- updated README.md current bounds and gap
- updated AGENTS.md note index if needed
- tests/verifier evidence

Deliverables on non-improvement:
- results/runs/<method>.json/logs
- negative result note with next strongest candidate
- no change to current best bounds
```
