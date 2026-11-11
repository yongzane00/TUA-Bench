# Reproducibility of the pilot tasks

Output of `python3 pilot/check_tasks.py jobs/pilot` on 2026-11-11 (oracle = reference fix, must score 1; nop = no
change, must score 0). The two failing tasks are listed in `excluded.md` and are not in the split.

| Task | Oracle (reference fix) | Nop (no change) | Grading time (s) | Reproducible |
|---|---|---|---|---|
| `django__django-7530` | 1, 1 | 1 | 42 | no |
| `django__django-9296` | 1, 1 | 0 | 102 | yes |
| `django__django-10097` | 0, 0 | 0 | 475 | no |
| `django__django-10880` | 1, 1 | 0 | 34 | yes |
| `django__django-10914` | 1, 1 | 0 | 52 | yes |
| `django__django-10973` | 1, 1 | 0 | 125 | yes |
| `django__django-10999` | 1, 1 | 0 | 41 | yes |
| `django__django-11066` | 1, 1 | 0 | 71 | yes |
| `django__django-11087` | 1, 1 | 0 | 42 | yes |
| `django__django-11095` | 1, 1 | 0 | 63 | yes |
| `django__django-11099` | 1, 1 | 0 | 66 | yes |
| `django__django-11119` | 1, 1 | 0 | 59 | yes |
| `django__django-11133` | 1, 1 | 0 | 43 | yes |
| `django__django-11141` | 1, 1 | 0 | 84 | yes |
| `django__django-11149` | 1, 1 | 0 | 74 | yes |
| `django__django-11163` | 1, 1 | 0 | 70 | yes |
| `django__django-11179` | 1, 1 | 0 | 53 | yes |
| `django__django-11206` | 1, 1 | 0 | 50 | yes |
| `django__django-11211` | 1, 1 | 0 | 70 | yes |
| `django__django-11239` | 1, 1 | 0 | 42 | yes |
| `django__django-11265` | 1, 1 | 0, 0 | 53 | yes |
| `django__django-11276` | 1, 1 | 0, 0 | 96 | yes |

Reproducible: 20 of 22 tasks checked. Grading time over 68 trials: median 41 s, P90 84 s.
