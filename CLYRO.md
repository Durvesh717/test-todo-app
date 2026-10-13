# CLYRO.md

<!-- Schema version: 1 -->

Deploy contract for **test-todo-app**, generated offline by the `clyro-scan`
skill in `--fix` mode on 2026-10-13. Clyro reads the ` ```yaml ` blocks below
and skips its live Step 1 scan. Everything here was read from the repo tree.
No secret values appear in this file.

## Summary

| | |
|---|---|
| Layout | Monorepo: Django backend at `./backend`, React (Vite) frontend at `./frontend` |
| Django project | `todoapp` (from `DJANGO_SETTINGS_MODULE` in `backend/manage.py`) |
| Resources | Django backend, React frontend, Celery worker + beat, PostgreSQL, Redis cache, S3 storage |
| Env vars | 10 total: 5 generated, 2 optional, 3 user secrets (1 agent-generatable, 2 third-party) |
| Compliance | 8/8 passing (after `--fix`) |
| Confidence | high |

## Resource graph

- **Backend**: Django 5.1.4 at `./backend`, project package `todoapp`, served by
  `gunicorn todoapp.wsgi:application`. A Dockerfile is committed
  (`backend/Dockerfile`), so Clyro uses it instead of generating one.
- **Frontend**: React 18 + Vite at `./frontend`. `npm run build` writes `dist/`.
- **Worker**: Celery 5.4 (`backend/todoapp/celery.py`), plus `django-celery-beat`,
  so scheduled tasks are on. The broker is **Redis**:
  `CELERY_BROKER_URL` falls back to `redis://localhost:6379/0` and nothing in the
  tree mentions SQS.
- **Database**: PostgreSQL (`psycopg2-binary`), read as one URL through
  `dj-database-url`.
- **Cache**: Redis through `django-redis` (`CACHES['default']` reads `REDIS_URL`).
- **Storage**: S3, because `boto3` + `django-storages` are installed and settings
  use `storages.backends.s3boto3.S3Boto3Storage` for `STORAGES['default']`.
  Static files use the local `StaticFilesStorage` backend.
- **Existing IaC**: none found.

```yaml
repository:
  is_monorepo: true
services:
  backend:
    detected: true
    framework: django
    path: ./backend
    project_name: todoapp
    wsgi_path: todoapp.wsgi:application
    dockerfile_found: true
    dockerfile_generated: false
  frontend:
    detected: true
    framework: react
    path: ./frontend
  worker:
    detected: true
    type: celery
    scheduled: true
    broker: redis
infrastructure:
  database:
    detected: true
    engine: postgres
    source: backend/requirements.txt
  cache:
    detected: true
    engine: redis
    source: backend/requirements.txt
  storage:
    detected: true
    type: s3
    source: settings
  queue:
    detected: false
    type: null
    source: null
existing_iac:
  found: false
  type: null
  path: null
```

## Environment variables

I walked every `*.py` under `backend/`, not only the settings files.
`STRIPE_SECRET_KEY` (`payments/views.py`) and `SENDGRID_API_KEY`
(`notifications/email.py`) are referenced outside settings, so a settings-only
scan would miss them.

| Key | Source | Classification | Hint |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | `backend/todoapp/settings/base.py` | user_secret | agent_generatable |
| `DEBUG` | `backend/todoapp/settings/base.py` | optional (default `False`) | |
| `ALLOWED_HOSTS` | `backend/todoapp/settings/base.py` | optional | |
| `DATABASE_URL` | `backend/todoapp/settings/base.py` | generated | |
| `CELERY_BROKER_URL` | `backend/todoapp/settings/base.py` | generated | |
| `CELERY_RESULT_BACKEND` | `backend/todoapp/settings/base.py` | generated | |
| `REDIS_URL` | `backend/todoapp/settings/base.py` | generated | |
| `AWS_STORAGE_BUCKET_NAME` | `backend/todoapp/settings/base.py` | generated | |
| `STRIPE_SECRET_KEY` | `backend/payments/views.py` | user_secret | third_party ([Stripe API keys](https://dashboard.stripe.com/apikeys)) |
| `SENDGRID_API_KEY` | `backend/notifications/email.py` | user_secret | third_party ([SendGrid API keys](https://app.sendgrid.com/settings/api_keys)) |

Notes:
- `REDIS_URL` is marked `generated`. Its source line (`'LOCATION': ...`) does
  not contain the word `CACHES`, but it sits inside the `CACHES` dict and holds
  the cache connection string, which Clyro's Redis provisions.
- `ALLOWED_HOSTS` defaults to `localhost,127.0.0.1` in code. That default is
  **not** safe for production, so `production_default` is `null`. Clyro must
  inject the ALB DNS name plus the task's private IP (or an equivalent).
- **`DJANGO_SETTINGS_MODULE`** is not in the list because the code sets it
  with `setdefault` to `todoapp.settings.dev`, which none of the access
  patterns matches. `backend/Dockerfile` now sets
  `ENV DJANGO_SETTINGS_MODULE=todoapp.settings.prod`, so the web and worker
  containers start with production settings. The `setdefault` calls leave an
  explicit value alone.
- AWS credentials for S3 are not read anywhere in code. boto3 uses the task
  role, which is the intended setup on Clyro.

```yaml
env_vars:
  - key: DJANGO_SECRET_KEY
    source: backend/todoapp/settings/base.py
    context: "SECRET_KEY = os.environ['DJANGO_SECRET_KEY']"
    classification: user_secret
    production_default: null
    hint: agent_generatable
  - key: DEBUG
    source: backend/todoapp/settings/base.py
    context: "DEBUG = os.environ.get('DEBUG', 'False') == 'True'"
    classification: optional
    production_default: "False"
  - key: ALLOWED_HOSTS
    source: backend/todoapp/settings/base.py
    context: "ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')"
    classification: optional
    production_default: null
  - key: DATABASE_URL
    source: backend/todoapp/settings/base.py
    context: "DATABASES = {'default': dj_database_url.parse(os.environ['DATABASE_URL'])}"
    classification: generated
    production_default: null
  - key: CELERY_BROKER_URL
    source: backend/todoapp/settings/base.py
    context: "CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')"
    classification: generated
    production_default: null
  - key: CELERY_RESULT_BACKEND
    source: backend/todoapp/settings/base.py
    context: "CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')"
    classification: generated
    production_default: null
  - key: REDIS_URL
    source: backend/todoapp/settings/base.py
    context: "'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),"
    classification: generated
    production_default: null
  - key: AWS_STORAGE_BUCKET_NAME
    source: backend/todoapp/settings/base.py
    context: "AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')"
    classification: generated
    production_default: null
  - key: STRIPE_SECRET_KEY
    source: backend/payments/views.py
    context: "stripe.api_key = os.environ['STRIPE_SECRET_KEY']"
    classification: user_secret
    production_default: null
    hint: third_party
    acquire_url: https://dashboard.stripe.com/apikeys
  - key: SENDGRID_API_KEY
    source: backend/notifications/email.py
    context: "sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))"
    classification: user_secret
    production_default: null
    hint: third_party
    acquire_url: https://app.sendgrid.com/settings/api_keys
```

## Compliance

All 8 applicable checks pass on the post-fix tree. Four failed before
`--fix` and were fixed in these commits:

| Check | Before | Fix commit |
|---|---|---|
| `allowed_hosts_env` | hardcoded `['localhost', '127.0.0.1']` | `67919c6` |
| `django_system_check` | `staticfiles.E005`: `STORAGES` had no `'staticfiles'` key | `2f30518` |
| `health_endpoint` | no health route; `SECURE_SSL_REDIRECT` would also 301 the ALB probe | `c5b5c55` |
| `dockerfile_registry` | `FROM python:3.12-slim` (Docker Hub) | `02dbe5f` |

Two more production fixes went in after the compliance gate passed:

| Problem | Fix commit |
|---|---|
| No `SECURE_PROXY_SSL_HEADER`, so traffic behind the ALB (TLS terminated there) hit an endless HTTPS redirect | `5d2e923` |
| The container defaulted to `todoapp.settings.dev` | `6e61641` |

How I verified: `python manage.py check` exits 0 under both
`todoapp.settings.dev` and `todoapp.settings.prod`.
`makemigrations --check --dry-run` reports no changes. Under prod settings, a
Django test client request for `GET /health` with `Host: 10.0.1.23` returned
200 over plain HTTP. A user request carrying `X-Forwarded-Proto: https`
returned 200 with no redirect loop.

**Conditional / not-applicable checks:** none. A Dockerfile is committed, so
`dockerfile_registry` applies. A React frontend was detected, so
`frontend_lockfile` and `frontend_build_script` apply. A database was detected,
so `database_url_env` applies.

```yaml
compliance_findings:
  - id: database_url_env
    title: Database configured from a single DATABASE_URL
    passed: true
    severity: blocker
    detail: settings/base.py builds DATABASES with dj_database_url.parse(os.environ['DATABASE_URL']); dj-database-url is in requirements.txt.
    fix_hint: null
  - id: allowed_hosts_env
    title: ALLOWED_HOSTS read from environment
    passed: true
    severity: warning
    detail: ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(','). Fixed in this run; it was previously hardcoded.
    fix_hint: null
  - id: django_migrations
    title: Every app with models has migrations
    passed: true
    severity: blocker
    detail: todos (the only app with models.py) has migrations/0001_initial.py. payments and notifications define no models. makemigrations --check reports no changes.
    fix_hint: null
  - id: health_endpoint
    title: Exposes a /health route
    passed: true
    severity: warning
    detail: >-
      todoapp/urls.py registers path('health', ...) returning 200 with no auth.
      prod.py exempts it from SECURE_SSL_REDIRECT (SECURE_REDIRECT_EXEMPT) so the
      ALB's plain-HTTP probe receives 200, not 301. Fixed in this run.
    fix_hint: null
  - id: dockerfile_registry
    title: Dockerfile base image not pulled from Docker Hub
    passed: true
    severity: warning
    detail: backend/Dockerfile uses FROM public.ecr.aws/docker/library/python:3.12-slim. Fixed in this run.
    fix_hint: null
  - id: django_system_check
    title: python manage.py check passes
    passed: true
    severity: blocker
    detail: >-
      manage.py check exits 0 under todoapp.settings.dev and todoapp.settings.prod
      after adding the missing 'staticfiles' STORAGES backend (was staticfiles.E005).
      check --deploy (prod) reports one warning only: security.W004 (SECURE_HSTS_SECONDS
      not set). That is hardening, not a blocker.
    fix_hint: null
  - id: frontend_lockfile
    title: Frontend lockfile committed
    passed: true
    severity: blocker
    detail: frontend/package-lock.json is tracked.
    fix_hint: null
  - id: frontend_build_script
    title: Frontend defines a build script
    passed: true
    severity: blocker
    detail: package.json scripts.build is "vite build", which outputs dist/.
    fix_hint: null
```

## Recommendations (outside the compliance gate)

- Consider setting `SECURE_HSTS_SECONDS` (`security.W004`) once HTTPS works
  end to end on the final domain. I left it unset on purpose: browsers cache
  HSTS, so turning it on too early is hard to undo.

## Metadata

```yaml
status: complete
block_reason: null
block_message: null
agent: "clyro-scan skill"
generated_at: "2026-10-13"
commit_sha: "6e6164179c65540e25fbc9da59f5aabed1c7010d"
scan_mode: fix
confidence: high
schema_version: 1
```
