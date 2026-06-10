# Goal Template — Improve TSP Lower Bound

Use this prompt with `/goal` from the TSP repo root.

```txt
/goal
Project: /home/werserk/3-education/hse/combinatorial-optimization/tsp

Primary objective:
Improve the verified lower bound for the 1114-city TSP challenge instance and reduce the current optimality gap.

Current best:
- lower_bound = 65493.4373688764
- lower_artifact = results/best/step9-held-karp-one-tree.json
- upper_bound = 73934
- upper_artifact = results/best/step6-lkh-best.json
- current interval = 65493.4373688764 <= OPT <= 73934
- current gap to lower = 12.887646411936071%

Success condition:
Produce a mathematically valid, independently verified lower bound strictly greater than 65493.4373688764, with a new best artifact under results/best/ and an updated gap calculation.

This is not a research-only goal. Research is required, but success requires metric improvement. If no improvement is found, stop only with an evidence-based exhaustion report.

Required skills and playbooks:
- Use skill: research-to-experiment-cycle.
- Follow docs/playbooks/tsp-lower-bound-improvement.md.
- Follow docs/playbooks/tsp-experiment-protocol.md.
- Apply docs/playbooks/tsp-result-review-gate.md before promoting any result.

Allowed methods:
- web research over papers, solver docs, GitHub, and benchmark reports;
- local open-source solver builds;
- Concorde/SCIP/HiGHS/QSopt/other relevant local solver attempts;
- improvements to our Held-Karp/Lagrangian 1-tree implementation;
- subtour LP/cutting-plane/relaxation approaches;
- multi-hour local runs.

Compute policy:
Aggressive local. Hours are acceptable; days, paid cloud, remote compute, destructive system-wide installs, or external submissions require user approval.

Required cycle per serious attempt:
1. Research sources and prior project artifacts.
2. Rank candidate methods by expected LB impact, validity, cost, and implementation risk.
3. Select the next candidate.
4. Write a proof/validity note before claiming any lower bound.
5. Implement or integrate with tests/verifiers.
6. Run bounded experiments with logs/artifacts.
7. Independently verify the candidate lower bound.
8. Promote only strict verified improvements; otherwise write a negative result note.

Priority tracks:
1. Strengthen Held-Karp/Lagrangian 1-tree ascent.
2. Try subtour LP / cutting-plane lower-bound route.
3. Use external reference solvers to estimate achievable LB and/or produce certificates.
4. Use weaker relaxations only if they feed one of the stronger tracks.

Stop conditions:
- verified LB improves above 65493.4373688764;
- three serious lower-bound tracks are exhausted with documented evidence;
- the next run exceeds aggressive-local compute budget;
- explicit user approval is needed;
- the selected approach is invalid for this TSP variant.

Deliverables on success:
- results/best/stepXX-<method>-lower-bound.json
- notes/stepXX-<method>-lower-bound.md or next numbered note
- updated README.md current bounds and gap
- updated AGENTS.md note index if needed
- tests/verifier evidence

Deliverables on non-improvement:
- results/runs/<method>.json/logs
- negative result note with next strongest candidate
- no change to current best bounds
```
