# Excluded tasks

Tasks that fail the reproducibility check (`check_tasks.py`): the reference fix must score 1 and no change must score
0. `select_tasks.py` skips every task listed here and takes the next candidate by its own rule.

| Task | Oracle (reference fix) | Nop (no change) | Why it cannot measure a fix |
|---|---|---|---|
| `django__django-7530` | 1, 1 | 1 | Its one FAIL_TO_PASS test (`test_squashmigrations_initial_attribute`) already passes on the untouched repo; first seen when a smoke trial scored 1 without changing any file |
| `django__django-10097` | 0, 0 | 0 | The reference fix itself fails (438 required tests, 475 s to grade), so no agent can pass it |
