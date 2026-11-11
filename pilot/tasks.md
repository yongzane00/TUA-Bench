Candidates after rules 1-3: 188 Django tasks. Dev families: 12; held-out families: 14; families shared: 8.

Dev, 20 tasks (2017-10-27 to 2019-04-24); the first 10 are the week-1 reproducible set:

| # | Task | Issue date | Difficulty | File changed by the reference patch | Family | Tests that must turn to pass |
|---|---|---|---|---|---|---|
| 1 | `django__django-9296` (week 1) | 2017-10-27 | <15 min fix | `django/core/paginator.py` | core | 1 |
| 2 | `django__django-10880` (week 1) | 2019-01-21 | <15 min fix | `django/db/models/aggregates.py` | db/models | 1 |
| 3 | `django__django-10914` (week 1) | 2019-01-30 | <15 min fix | `django/conf/global_settings.py` | conf | 1 |
| 4 | `django__django-10973` (week 1) | 2019-02-11 | 15 min - 1 hour | `django/db/backends/postgresql/client.py` | db/backends | 5 |
| 5 | `django__django-10999` (week 1) | 2019-02-16 | <15 min fix | `django/utils/dateparse.py` | utils | 2 |
| 6 | `django__django-11066` (week 1) | 2019-03-09 | <15 min fix | `django/contrib/contenttypes/management/__init__.py` | contrib/contenttypes | 1 |
| 7 | `django__django-11087` (week 1) | 2019-03-16 | 15 min - 1 hour | `django/db/models/deletion.py` | db/models | 1 |
| 8 | `django__django-11095` (week 1) | 2019-03-19 | 15 min - 1 hour | `django/contrib/admin/options.py` | contrib/admin | 1 |
| 9 | `django__django-11099` (week 1) | 2019-03-20 | <15 min fix | `django/contrib/auth/validators.py` | contrib/auth | 3 |
| 10 | `django__django-11119` (week 1) | 2019-03-24 | <15 min fix | `django/template/engine.py` | template | 1 |
| 11 | `django__django-11133` | 2019-03-27 | <15 min fix | `django/http/response.py` | http | 1 |
| 12 | `django__django-11141` | 2019-03-28 | 15 min - 1 hour | `django/db/migrations/loader.py` | db/migrations | 1 |
| 13 | `django__django-11149` | 2019-03-30 | 15 min - 1 hour | `django/contrib/admin/options.py` | contrib/admin | 2 |
| 14 | `django__django-11163` | 2019-04-02 | <15 min fix | `django/forms/models.py` | forms | 1 |
| 15 | `django__django-11179` | 2019-04-05 | <15 min fix | `django/db/models/deletion.py` | db/models | 1 |
| 16 | `django__django-11206` | 2019-04-13 | 15 min - 1 hour | `django/utils/numberformat.py` | utils | 2 |
| 17 | `django__django-11211` | 2019-04-13 | 15 min - 1 hour | `django/db/models/fields/__init__.py` | db/models | 1 |
| 18 | `django__django-11239` | 2019-04-16 | <15 min fix | `django/db/backends/postgresql/client.py` | db/backends | 1 |
| 19 | `django__django-11265` | 2019-04-21 | 15 min - 1 hour | `django/db/models/sql/query.py` | db/models | 1 |
| 20 | `django__django-11276` | 2019-04-24 | 15 min - 1 hour | `django/utils/html.py` | utils | 26 |

Held-out, 40 tasks (2022-01-27 to 2023-07-17); not used for any tuning:

| # | Task | Issue date | Difficulty | File changed by the reference patch | Family | Tests that must turn to pass |
|---|---|---|---|---|---|---|
| 1 | `django__django-15368` | 2022-01-27 | <15 min fix | `django/db/models/query.py` | db/models | 1 |
| 2 | `django__django-15380` | 2022-01-31 | <15 min fix | `django/db/migrations/autodetector.py` | db/migrations | 1 |
| 3 | `django__django-15382` | 2022-02-01 | 15 min - 1 hour | `django/db/models/expressions.py` | db/models | 1 |
| 4 | `django__django-15499` | 2022-03-10 | <15 min fix | `django/db/migrations/operations/models.py` | db/migrations | 1 |
| 5 | `django__django-15525` | 2022-03-18 | 15 min - 1 hour | `django/core/serializers/base.py` | core/serializers | 1 |
| 6 | `django__django-15569` | 2022-04-08 | <15 min fix | `django/db/models/query_utils.py` | db/models | 2 |
| 7 | `django__django-15572` | 2022-04-09 | <15 min fix | `django/template/autoreload.py` | template | 1 |
| 8 | `django__django-15695` | 2022-05-16 | 15 min - 1 hour | `django/db/migrations/operations/models.py` | db/migrations | 1 |
| 9 | `django__django-15731` | 2022-05-24 | 15 min - 1 hour | `django/db/models/manager.py` | db/models | 1 |
| 10 | `django__django-15732` | 2022-05-24 | 15 min - 1 hour | `django/db/backends/base/schema.py` | db/backends | 1 |
| 11 | `django__django-15741` | 2022-05-28 | <15 min fix | `django/utils/formats.py` | utils | 2 |
| 12 | `django__django-15863` | 2022-07-20 | <15 min fix | `django/template/defaultfilters.py` | template | 1 |
| 13 | `django__django-15930` | 2022-08-07 | <15 min fix | `django/db/models/expressions.py` | db/models | 1 |
| 14 | `django__django-15973` | 2022-08-19 | 15 min - 1 hour | `django/db/migrations/autodetector.py` | db/migrations | 1 |
| 15 | `django__django-15987` | 2022-08-23 | <15 min fix | `django/core/management/commands/loaddata.py` | core/management | 1 |
| 16 | `django__django-16082` | 2022-09-21 | 15 min - 1 hour | `django/db/models/expressions.py` | db/models | 2 |
| 17 | `django__django-16116` | 2022-09-25 | <15 min fix | `django/core/management/commands/makemigrations.py` | core/management | 1 |
| 18 | `django__django-16136` | 2022-09-29 | 15 min - 1 hour | `django/views/generic/base.py` | views/generic | 2 |
| 19 | `django__django-16139` | 2022-09-30 | <15 min fix | `django/contrib/auth/forms.py` | contrib/auth | 1 |
| 20 | `django__django-16145` | 2022-10-03 | <15 min fix | `django/core/management/commands/runserver.py` | core/management | 1 |
| 21 | `django__django-16255` | 2022-11-04 | <15 min fix | `django/contrib/sitemaps/__init__.py` | contrib/sitemaps | 1 |
| 22 | `django__django-16333` | 2022-11-27 | <15 min fix | `django/contrib/auth/forms.py` | contrib/auth | 1 |
| 23 | `django__django-16429` | 2023-01-05 | <15 min fix | `django/utils/timesince.py` | utils | 4 |
| 24 | `django__django-16454` | 2023-01-15 | 15 min - 1 hour | `django/core/management/base.py` | core/management | 1 |
| 25 | `django__django-16485` | 2023-01-18 | 15 min - 1 hour | `django/template/defaultfilters.py` | template | 1 |
| 26 | `django__django-16493` | 2023-01-20 | 15 min - 1 hour | `django/db/models/fields/files.py` | db/models | 1 |
| 27 | `django__django-16502` | 2023-01-26 | 15 min - 1 hour | `django/core/servers/basehttp.py` | core/servers | 1 |
| 28 | `django__django-16527` | 2023-02-05 | 15 min - 1 hour | `django/contrib/admin/templatetags/admin_modify.py` | contrib/admin | 1 |
| 29 | `django__django-16569` | 2023-02-17 | <15 min fix | `django/forms/formsets.py` | forms | 2 |
| 30 | `django__django-16595` | 2023-02-24 | <15 min fix | `django/db/migrations/operations/fields.py` | db/migrations | 1 |
| 31 | `django__django-16612` | 2023-03-02 | 15 min - 1 hour | `django/contrib/admin/sites.py` | contrib/admin | 2 |
| 32 | `django__django-16662` | 2023-03-18 | 15 min - 1 hour | `django/db/migrations/writer.py` | db/migrations | 1 |
| 33 | `django__django-16667` | 2023-03-20 | 15 min - 1 hour | `django/forms/widgets.py` | forms | 2 |
| 34 | `django__django-16801` | 2023-04-26 | <15 min fix | `django/db/models/fields/files.py` | db/models | 1 |
| 35 | `django__django-16819` | 2023-05-01 | 15 min - 1 hour | `django/db/migrations/operations/models.py` | db/migrations | 1 |
| 36 | `django__django-16877` | 2023-05-19 | 15 min - 1 hour | `django/template/defaultfilters.py` | template | 4 |
| 37 | `django__django-16899` | 2023-05-26 | <15 min fix | `django/contrib/admin/checks.py` | contrib/admin | 2 |
| 38 | `django__django-16901` | 2023-05-30 | 15 min - 1 hour | `django/db/models/sql/where.py` | db/models | 1 |
| 39 | `django__django-17029` | 2023-06-29 | <15 min fix | `django/apps/registry.py` | apps | 1 |
| 40 | `django__django-17087` | 2023-07-17 | <15 min fix | `django/db/migrations/serializer.py` | db/migrations | 1 |

```text
# dev
django__django-9296
django__django-10880
django__django-10914
django__django-10973
django__django-10999
django__django-11066
django__django-11087
django__django-11095
django__django-11099
django__django-11119
django__django-11133
django__django-11141
django__django-11149
django__django-11163
django__django-11179
django__django-11206
django__django-11211
django__django-11239
django__django-11265
django__django-11276
# held-out
django__django-15368
django__django-15380
django__django-15382
django__django-15499
django__django-15525
django__django-15569
django__django-15572
django__django-15695
django__django-15731
django__django-15732
django__django-15741
django__django-15863
django__django-15930
django__django-15973
django__django-15987
django__django-16082
django__django-16116
django__django-16136
django__django-16139
django__django-16145
django__django-16255
django__django-16333
django__django-16429
django__django-16454
django__django-16485
django__django-16493
django__django-16502
django__django-16527
django__django-16569
django__django-16595
django__django-16612
django__django-16662
django__django-16667
django__django-16801
django__django-16819
django__django-16877
django__django-16899
django__django-16901
django__django-17029
django__django-17087
```
