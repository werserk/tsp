# Step 2 — базовая инфраструктура

Дата: 2026-06-09

## Вывод

Создано и отрефакторено минимальное ядро для дальнейшей работы над bounds:

- загрузка матриц;
- определение формата матрицы;
- централизованные project constants;
- общие типы `Matrix`, `Tour`, `City`, `Distance`;
- custom exceptions для parse/validation ошибок;
- валидация матриц;
- валидация tour;
- независимый пересчёт длины tour;
- fast path `tour_length(..., validate=False)` для будущих горячих циклов;
- smoke checks на реальных входных файлах.

## Реализованные файлы

```txt
src/
  __init__.py
  io/
    __init__.py
    exceptions.py
    matrix_loader.py
    validation.py
  tsp/
    __init__.py
    constants.py
    tour.py
    types.py

tests/
  conftest.py
  test_step2_core.py
  test_step2_refactor_contract.py

experiments/
  step2_smoke_checks.py
```

## Константы

```python
from src.tsp.constants import (
    CHALLENGE_CITY_COUNT,
    CHALLENGE_MATRIX_PATH,
    LECTURE_SAMPLE_CITY_COUNT,
    LECTURE_SAMPLE_MATRIX_PATH,
    MATRIX_FORMAT_PLAIN_WITH_SIZE,
    MATRIX_FORMAT_PYTHON_LITERAL,
)
```

Canonical challenge constants:

```python
CHALLENGE_CITY_COUNT = 1114
CHALLENGE_MATRIX_PATH = Path("data/raw/matrices/M.txt")
```

## API

### `load_matrix`

```python
from src.io.matrix_loader import load_matrix

data = load_matrix("data/raw/matrices/M.txt")
```

Возвращает `MatrixData`:

```python
MatrixData(
    matrix=Matrix,
    n=int,
    source_path=Path,
    format=str,
)
```

Поддержанные форматы:

- `MATRIX_FORMAT_PLAIN_WITH_SIZE` — `M.txt`;
- `MATRIX_FORMAT_PYTHON_LITERAL` — `tsp_matrix1.txt`.

Ошибки парсинга дают `MatrixParseError`.

### `detect_matrix_format`

```python
from src.io.matrix_loader import detect_matrix_format

matrix_format = detect_matrix_format(text)
```

Формат определяется один раз и дальше dispatch-ится на соответствующий parser.

### `validate_matrix`

```python
from src.io.validation import validate_matrix

validate_matrix(matrix)
```

Проверяет:

- матрица непустая;
- матрица квадратная;
- нет отрицательных расстояний;
- диагональ нулевая;
- матрица симметричная по умолчанию.

Ошибки дают `MatrixValidationError`.

### `validate_tour`

```python
from src.io.validation import validate_tour

validate_tour(tour, n)
```

Контракт tour:

```python
[0, 5, 2, 1]
```

означает цикл:

```txt
0 → 5 → 2 → 1 → 0
```

Стартовый город в конце не дублируется. Возврат в старт считается неявно.

Ошибки дают `TourValidationError`.

### `tour_length`

```python
from src.tsp.tour import tour_length

length = tour_length(matrix, tour)
```

По умолчанию сначала валидирует матрицу и tour, затем считает длину цикла с неявным возвратом в старт.

Для горячих циклов алгоритмов можно отключить повторную проверку уже валидированной матрицы/tour:

```python
length = tour_length(matrix, tour, validate=False)
```

Финальный reported tour всё равно надо пересчитывать с `validate=True`.

## Проверки

Unit tests:

```bash
pytest -q
```

Результат:

```txt
19 passed
```

Smoke checks:

```bash
python experiments/step2_smoke_checks.py
```

Результат:

```json
[
  {
    "file": "data/raw/matrices/M.txt",
    "format": "plain_with_size",
    "n": 1114,
    "sequential_tour_length": 2081212
  },
  {
    "file": "data/raw/matrices/tsp_matrix1.txt",
    "format": "python_literal",
    "n": 94,
    "sequential_tour_length": 276137
  }
]
```

## Практическое значение

Теперь любой будущий upper bound можно проверять независимо:

1. загрузить ту же матрицу;
2. проверить, что tour посещает все `1114` городов ровно один раз;
3. пересчитать длину;
4. сохранить результат с metadata.

Это защищает от типичных ошибок:

- неверный формат входного файла;
- off-by-one индексация;
- повтор города в tour;
- пропущенный город;
- забытый возврат в старт;
- неверно посчитанная длина.

## Следующий шаг

Step 3: получить первый upper bound.

Минимальный pipeline:

1. `nearest neighbor` из нескольких стартов;
2. проверка tour через `validate_tour`;
3. независимый пересчёт через `tour_length`;
4. сохранение результата в `results/best/`.
