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

## Текущий лучший upper bound

```txt
algorithm: nearest_neighbor_multi_start
length: 88839
start_city: 219
artifact: results/best/step3-nearest-neighbor-best.json
```

## Следующий шаг

1. Улучшить upper bound через 2-opt local search от текущего best tour.
2. Проверить tour через `validate_tour` и пересчитать длину через `tour_length`.
3. Сохранить новый лучший результат в `results/best/`.
