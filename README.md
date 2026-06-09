# TSP Project — Combinatorial Optimization

Цель: получить как можно лучшие **upper bound** и **lower bound** для TSP challenge на 1114 городов, используя приложенную матрицу расстояний, и подготовить 15-минутное объяснение кода/результатов к 16 июня.

## Структура

```txt
data/
  raw/archives/       # оригинальные zip-файлы от лектора, не менять
  raw/matrices/       # распакованные матрицы расстояний
  processed/          # нормализованные/кэшированные данные для быстрых запусков
src/
  io/                 # загрузка и валидация матриц
  heuristics/         # upper bound: nearest-neighbor, insertion, local search, LK-подобные улучшения
  bounds/             # lower bound: MST/1-tree/assignment/relaxations
experiments/          # воспроизводимые сценарии запусков и конфиги
results/
  runs/               # сырые логи отдельных запусков
  best/               # лучшие найденные туры, bounds, короткие отчеты
notebooks/            # разведочный анализ, графики, проверки
notes/                # рабочие заметки, план объяснения у доски
references/
  lecturer-code/      # исходные Python-файлы от лектора
  literature/         # статьи/материалы
```

## Первые правила работы

- `data/raw/**` считать read-only.
- Каждый запуск, который дал новый лучший результат, сохранять в `results/best/` с датой, параметрами и seed.
- Эксперименты делать воспроизводимыми: фиксировать seed, команду запуска, входную матрицу и версию алгоритма.
- Рабочий challenge-файл: `data/raw/matrices/M.txt` — матрица расстояний `1114×1114`.

## Учебные заметки

- `notes/00-lecturer-brief.md` — формулировка задания от лектора.
- `notes/01-tsp-basics-and-development-plan.md` — базовое объяснение TSP, upper/lower bounds и первый план разработки.
- `notes/02-step1-data-audit.md` — аудит входных матриц: формат, размерность, симметрия, диапазоны, ограничения.
- `notes/03-step2-core-infrastructure.md` — загрузчик матриц, валидация tour, пересчёт длины, smoke checks.
- `notes/04-step3-nearest-neighbor-baseline.md` — первый валидный upper bound: nearest-neighbor multi-start, length `88839`.
- `notes/05-step4-two-opt-improvement.md` — 2-opt improvement, новый upper bound `80585`.
- `notes/06-step5-lower-bound-mst-one-tree.md` — MST / 1-tree lower bound, proof and current interval.
- `notes/07-next-experiments-plan.md` — prioritized SOTA/baseline experiment plan.
- `notes/08-step6-lkh-benchmark.md` — LKH benchmark, new best upper bound `73934`.
- `notes/09-step7-several-root-one-tree.md` — sampled several-root 1-tree lower bound, new lower bound `63494`.

## Текущие bounds

```txt
lower_bound: 63494
upper_bound: 73934
interval: 63494 <= OPT <= 73934
absolute_gap: 10440
relative_gap: 14.12%
```

Artifacts:

```txt
upper: results/best/step6-lkh-best.json
lower: results/best/step7-several-root-one-tree.json
```

## Следующий шаг

1. Запустить LKH с несколькими seeds / RUNS для усиления upper bound.
2. Или усилить lower bound дальше: Held-Karp-style 1-tree penalties.
3. Каждый новый best сохранять в `results/best/` и пересчитывать/обосновывать независимо.
