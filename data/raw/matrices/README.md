# Raw matrices

## Observed files

| File | Format | Declared size | Parsed rows | Parsed columns | Note |
|---|---|---:|---:|---:|---|
| `M.txt` | plain matrix with first-line size | 1114 | 1114 | 1114 | Main challenge input; canonical size is 1114 cities. |
| `tsp_matrix1.txt` | Python literal `M=[[...]]` | — | 94 | 94 | Older/smaller class example; format differs from `M.txt`. |

Both observed matrices are symmetric, have zero diagonal, no negative values, and no off-diagonal zero distances.

Full audit:

- `../../processed/step1-data-audit.json`
- `../../../notes/02-step1-data-audit.md`

Do not edit these files directly. Normalized derivatives go to `data/processed/`.
