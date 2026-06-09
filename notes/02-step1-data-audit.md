# Step 1 — аудит входных данных

Дата: 2026-06-09

## Вывод

Основной challenge-файл для работы: `data/raw/matrices/M.txt`. Canonical challenge size: `1114` городов.

Он корректно парсится как квадратная симметричная матрица расстояний `1114×1114`:

- первая строка объявляет размер `1114`;
- далее идут `1114` строк по `1114` целых чисел;
- диагональ нулевая;
- отрицательных расстояний нет;
- вне диагонали нулей нет;
- матрица симметрична.

## Проверенные файлы

| File | Format | Shape | Declared size | Symmetric | Diagonal | Negatives | Off-diagonal zeros | Off-diagonal range |
|---|---|---:|---:|---|---|---:|---:|---:|
| `data/raw/matrices/M.txt` | plain matrix with first-line size | `1114×1114` | `1114` | yes | all zero | 0 | 0 | `2..7902` |
| `data/raw/matrices/tsp_matrix1.txt` | Python literal `M=[[...]]` | `94×94` | — | yes | all zero | 0 | 0 | `66..7861` |

Raw machine-readable audit:

- `data/processed/step1-data-audit.json`

Reproducible audit script:

- `experiments/step1_data_audit.py`

Run:

```bash
python experiments/step1_data_audit.py
```

## Формат `M.txt`

`M.txt` имеет формат:

```txt
1114
0 151 2464 ...
151 0 2408 ...
...
```

То есть:

1. первая строка — размер `n`;
2. следующие `n` строк — строки матрицы;
3. значения разделены пробелами;
4. индексация в файле не указана, поэтому в коде используем 0-based индексы Python: `0..1113`.

## Формат `tsp_matrix1.txt`

`tsp_matrix1.txt` имеет другой формат:

```python
M=[[0, 4644, ...],
   [4644, 0, ...],
   ...]
```

Это не такой же plain text format, как `M.txt`, а Python literal/assignment. Для общего загрузчика нужно поддержать оба формата или явно пометить `tsp_matrix1.txt` как lecture/example input.

## Метрика и triangle inequality

Обе матрицы симметричны, но в проверке найдены нарушения triangle inequality.

Пример для `M.txt`:

```txt
d(8, 26) = 3755
переход через 12: d(8, 12) + d(12, 26) = 1990 + 1764 = 3754
3755 > 3754
```

Это значит: нельзя молча считать задачу “геометрической” или “metric TSP”.

Практический эффект:

- `nearest neighbor`, `2-opt`, `3-opt` всё ещё можно использовать как эвристики;
- нельзя опираться на свойства евклидовой плоскости или triangle inequality без проверки;
- lower bound методы должны быть корректны для общей симметричной TSP-матрицы, а не только для metric TSP.

## Что это значит для разработки

### Для загрузчика

Нужны два режима:

1. `plain_with_size` для `M.txt`;
2. `python_literal` для `tsp_matrix1.txt`.

Минимальный контракт загрузчика:

- вернуть квадратную матрицу `n×n`;
- сохранить `n`;
- проверить uniform row length;
- проверить диагональ;
- проверить отсутствие отрицательных значений;
- проверить симметричность, если алгоритм предполагает symmetric TSP.

### Для upper bound

Первый рабочий pipeline:

1. загрузить `M.txt`;
2. построить tour;
3. проверить, что tour содержит все вершины `0..1113` ровно один раз;
4. пересчитать длину tour независимо от алгоритма;
5. сохранить результат с metadata.

### Для lower bound

Можно начинать с методов для symmetric TSP:

- MST bound;
- 1-tree bound.

Нельзя формулировать доказательство через metric assumptions, если метод их требует. В текущих данных triangle inequality не гарантирована.

## Следующий шаг

Step 2: сделать базовую инфраструктуру в `src/`:

- `src/io/matrix_loader.py` — загрузка `M.txt` и `tsp_matrix1.txt`;
- `src/io/validation.py` — проверки матрицы и tour;
- функция длины маршрута;
- минимальные тесты/самопроверки на обеих матрицах.
