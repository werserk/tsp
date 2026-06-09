# Step 4 — 2-opt local search upper-bound improvement

Дата: 2026-06-09

## Вывод

Улучшен текущий upper bound после Step 3:

```txt
previous best = 88839
new best = 80585
improvement = 8254
algorithm = two_opt_first_improvement
moves_applied = 268
passes = 269
```

Результат сохранён:

```txt
results/best/step4-two-opt-best.json
```

## Что запускалось

```bash
python experiments/step4_two_opt_baseline.py
```

Input:

```txt
data/raw/matrices/M.txt
n = 1114
```

Source artifact:

```txt
results/best/step3-nearest-neighbor-best.json
```

## Алгоритм

Использован deterministic 2-opt local search со стратегией `first_improvement`.

Один 2-opt move:

```txt
... a → b ... c → d ...
```

заменяет два ребра:

```txt
a → b, c → d
```

на:

```txt
a → c, b → d
```

и разворачивает segment между `b` и `c`.

Delta считается без полного пересчёта tour:

```python
added - removed
```

где:

```python
removed = d(a, b) + d(c, d)
added = d(a, c) + d(b, d)
```

После завершения финальный tour всё равно пересчитывается независимо через:

```python
tour_length(matrix, result.tour, validate=True)
```

## Реализованные файлы

```txt
src/heuristics/two_opt.py
experiments/step4_two_opt_baseline.py
tests/test_step4_two_opt.py
results/best/step4-two-opt-best.json
```

## API

```python
from src.heuristics.two_opt import improve_tour_two_opt

result = improve_tour_two_opt(matrix, initial_tour)
```

Result shape:

```python
TwoOptResult(
    algorithm="two_opt_first_improvement",
    initial_length=int,
    length=int,
    tour=list[int],
    moves_applied=int,
    passes=int,
    metadata={"strategy": "first_improvement"},
)
```

## Проверка результата

Artifact check:

```txt
algorithm two_opt_first_improvement
n 1114
initial_length 88839
length 80585
improvement 8254
moves_applied 268
passes 269
tour_len 1114
unique_tour_len 1114
```

Unit tests:

```txt
pytest -q
28 passed
```

## Практическое значение

`80585` — новый защищённый upper bound.

Это уже лучше nearest-neighbor baseline на:

```txt
8254
```

или примерно:

```txt
9.29%
```

## Ограничения

- Это still local optimum только для текущей deterministic first-improvement траектории.
- Не гарантирует глобальный optimum.
- Может быть улучшено multi-start 2-opt, randomized restarts, insertion heuristics, 3-opt или Lin-Kernighan-like moves.

## Следующий шаг

Step 5: получить ещё более сильный upper bound.

Практичный вариант:

```txt
multi-start nearest-neighbor → 2-opt для каждого старта → выбрать лучший
```

Это дороже, но всё ещё реалистично для `1114` городов. Альтернатива: lower bound baseline через MST/1-tree, если нужно начать готовить вторую часть задания.
