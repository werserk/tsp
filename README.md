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
- `notes/10-step8-multistart-two-opt.md` — own NN-ranked multi-start 2-opt check, length `77771`.
- `notes/11-step9-held-karp-one-tree.md` — Held-Karp-style Lagrangian 1-tree penalties, new lower bound `65493.437369`.
- `notes/12-step10-restricted-three-opt.md` — restricted 3-opt/LK-like check on LKH tour; no improvement over `73934`.
- `notes/13-step11-lkh-multiseed.md` — LKH seeds `1-20`, `RUNS=1`; no improvement over `73934`.
- `notes/14-step12-lkh-portfolio-plan.md` — bounded LKH portfolio runner plan with ETA/progress/resume.
- `notes/14-step12-lkh-portfolio.md` — Step 12 smoke portfolio report; runner ready for longer quality-first waves.

## Текущие bounds

```txt
lower_bound: 65493.437369
upper_bound: 73934
interval: 65493.437369 <= OPT <= 73934
integer interval: 65494 <= OPT <= 73934
absolute_gap: 8440.562631
relative_gap: 11.42%
```

Artifacts:

```txt
upper: results/best/step6-lkh-best.json
lower: results/best/step9-held-karp-one-tree.json
```

## Следующий шаг

1. Запустить bounded Step 12 LKH portfolio wave через `experiments/step12_lkh_portfolio.py` с `--time-budget-hours` и `--job-timeout-minutes`.
2. Если portfolio найдёт `< 73934`, сохранить новый verified best в `results/best/step12-lkh-portfolio-best.json` и обновить interval.
3. Если improvement нет, выбрать 1-2 лучших configs по `results/runs/step12-lkh-portfolio-report.html` для targeted long wave или переключиться на финальное объяснение.
4. Каждый новый best сохранять в `results/best/` и пересчитывать/обосновывать независимо.
