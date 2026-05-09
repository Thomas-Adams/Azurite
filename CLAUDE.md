# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Azurite** is a full-stack image review and management system for AI-generated images (primarily from Stable Diffusion). It consists of:

- **Backend**: FastAPI-based image importer service with PostgreSQL database, MinIO object storage, and Meilisearch full-text search
- **Frontend**: SvelteKit web application with Tailwind CSS for reviewing, searching, and browsing generated images

The system captures image metadata from ComfyUI workflows, stores generation parameters, uploads images to MinIO, and provides an interface for rating, reviewing, and searching images.

## Repository Structure

```
Azurite/
├── image-review/          # SvelteKit frontend application
│   ├── src/
│   │   ├── routes/        # SvelteKit pages (+page.svelte, +layout.svelte)
│   │   │   ├── +page.svelte (home)
│   │   │   ├── review/+page.svelte (image carousel + review interface)
│   │   │   ├── search/+page.svelte (full-text search with thumbnail grid)
│   │   │   └── config/+page.svelte (configuration: IMAGE_ROOT setting)
│   │   ├── lib/
│   │   │   ├── components/custom/ (ReviewDialog, ReviewNavigationBar, ui-types)
│   │   │   └── components/ui/ (skeleton UI library dialogs)
│   │   └── app.html
│   ├── e2e/               # Playwright end-to-end tests
│   │   ├── navigation.spec.ts
│   │   ├── search-page.spec.ts
│   │   └── config-page.spec.ts
│   ├── playwright.config.ts
│   ├── package.json, pnpm-workspace.yaml, tsconfig.json
│   ├── vite.config.ts, svelte.config.js, tailwindcss.config.js
│   └── .svelte-kit/ (generated)
│
├── services/image-importer/  # FastAPI backend service
│   ├── api/
│   │   ├── app.py (all routes)
│   │   ├── state.py (FastAPI app config, static folders, CORS)
│   │   ├── main.py (explicit re-exports)
│   │   ├── tasks.py (background task: run_scan with WebSocket progress)
│   │   ├── websocket.py (ConnectionManager for job progress updates)
│   │   └── templates/ (Jinja2 templates: listing.html)
│   ├── models/ (SQLAlchemy ORM models, pony_image schema)
│   │   ├── base.py (Base, EntityBaseMixin with id, created_at, updated_at)
│   │   ├── image.py (Image: file metadata, width, height, sha256)
│   │   ├── generation.py (Generation: prompts, cfg, seed, steps, model_name)
│   │   ├── lora.py, lora_image.py (LORA model parameters)
│   │   ├── review.py (Review: rating, comment)
│   │   ├── storage.py (Storage: MinIO bucket info, sha256 index)
│   │   ├── settings.py (Settings: persisted app config — single row)
│   │   ├── meta_data.py (MetaData: raw PNG metadata JSON)
│   │   └── workflow.py
│   ├── services/
│   │   ├── image_importer.py (core logic: metadata parsing, import, MinIO upload)
│   │   └── settings_service.py (get_settings / update_settings with DB persistence)
│   ├── search/
│   │   ├── client.py (Meilisearch client, ensure_index)
│   │   └── indexer.py (build_document, index_review)
│   ├── scripts/
│   │   └── backfill_search_index.py (index all existing reviewed images)
│   ├── utils/
│   │   ├── image_sha.py (sha256 hashing)
│   │   ├── image_utils.py (image dimension reading)
│   │   └── excerpt_parser.py (ComfyUI metadata extraction)
│   ├── database/ (AsyncSession factory, engine setup)
│   ├── config/ (Settings via Pydantic — all env vars use AZURITE_ prefix)
│   ├── storage/ (MinIO client config)
│   ├── dto/ (request/response DTOs)
│   ├── alembic/ (database migrations)
│   ├── tests/ (pytest suite — 141 tests, 80% coverage)
│   ├── .venv/ (Python virtual environment — local to service)
│   ├── requirements.txt
│   └── alembic.ini, pytest.ini, reset_migrations.sh
│
├── database/ (root-level database scripts)
└── CLAUDE.md
```

## Key Technologies

**Frontend:**
- Svelte 5 (runes mode) with SvelteKit
- Tailwind CSS 4 with typography and forms plugins
- `lib/components/ui/` — shadcn-svelte components, managed via `jsrepo`; Bits UI is the headless primitive
- `lib/components/custom/` — hand-written components using `@skeletonlabs/skeleton-svelte` (Dialog, Carousel, Pagination, Navigation)
- Playwright for end-to-end tests
- TypeScript 6

**Backend:**
- FastAPI 0.135+ with Uvicorn
- SQLAlchemy 2 async ORM with PostgreSQL (asyncpg)
- Alembic for database migrations
- MinIO 7 for object storage (S3-compatible)
- Meilisearch (v1.43+) for full-text search
- Pydantic 2 / pydantic-settings for validation and config

**Database:**
- PostgreSQL with schema: `pony_image`
- Tables: image, generation, lora, review, storage, meta_data, workflow, lora_image, settings
- Unique constraint on `image.sha256` (deduplication)
- `storage.sha256` indexed for cross-directory duplicate detection

## Development Setup

### Backend (Python)

1. **Virtual environment**: Local to the service at `services/image-importer/.venv/`
   ```bash
   cd services/image-importer
   python -m venv .venv && .venv/bin/pip install -r requirements.txt
   ```

2. **Database setup**:
   - PostgreSQL running on localhost:5432
   - Database: `pony`, Schema: `pony_image`
   - User: `pony_admin` / password: `admin`
   - Run migrations: `cd services/image-importer && .venv/bin/alembic upgrade head`
   - **Important**: When adding a new model, import it in `alembic/env.py` so autogenerate detects it

3. **MinIO setup**:
   - MinIO on localhost:9000 (S3 API), localhost:9001 (console)
   - Credentials: `admin` / `12345678`
   - Buckets are auto-created with a public `s3:GetObject` policy via `ensure_bucket()`

4. **Meilisearch setup**:
   - Run: `./meilisearch --master-key='meili@goe-nostromo-04'`
   - Listens on localhost:7700
   - Backfill existing reviews: `cd services/image-importer && .venv/bin/python scripts/backfill_search_index.py`

5. **Environment variables** (in `services/image-importer/.env`):
   ```
   AZURITE_IMAGE_ROOT=/mnt/windows/stablediffusion
   AZURITE_DB_HOST=localhost
   AZURITE_DB_PORT=5432
   AZURITE_DB_NAME=pony
   AZURITE_DB_USER=pony_admin
   AZURITE_DB_PASSWORD=admin
   AZURITE_DB_SCHEMA=pony_image
   AZURITE_MINIO_ENDPOINT=localhost:9000
   AZURITE_MINIO_ACCESS_KEY=admin
   AZURITE_MINIO_SECRET_KEY=12345678
   AZURITE_MINIO_BUCKET=tsukuyomi
   AZURITE_MEILI_HOST=http://localhost:7700
   AZURITE_MEILI_API_KEY=meili@goe-nostromo-04
   ```
   Note: `IMAGE_ROOT` is also persisted in the `settings` DB table and readable/writable via `GET/PUT /api/settings`. The DB value takes precedence at request time; the env var is used to seed the default on first start.

6. **Run API server**:
   ```bash
   cd services/image-importer
   .venv/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Testing (Backend)

Run all tests (from service directory):
```bash
cd services/image-importer
.venv/bin/python -m pytest
```

Produces:
- Terminal coverage summary (80% target)
- `reports/coverage/` — HTML coverage report
- `reports/test-report.html` — HTML test report

Run a single file:
```bash
.venv/bin/python -m pytest tests/test_settings.py
```

**Test strategy**: All tests are pure-unit or use `tmp_path` fixtures. DB and MinIO are mocked. FastAPI endpoints tested via `httpx.AsyncClient` + `ASGITransport`.

### Frontend (Node/pnpm)

1. **Install dependencies**:
   ```bash
   cd image-review
   pnpm install
   ```

2. **Run development server**:
   ```bash
   pnpm dev  # http://localhost:5173
   ```

3. **Type check**:
   ```bash
   pnpm check
   ```

4. **Run e2e tests** (requires dev server or `webServer` auto-start):
   ```bash
   pnpm test:e2e            # headless
   pnpm test:e2e:ui         # interactive UI mode
   ```
   Tests live in `e2e/`. They mock API routes via `page.route()` so no live backend is needed for most tests.

5. **CORS**: Frontend (`http://localhost:5173`) is whitelisted in `api/state.py`

## API Routes

**Image Listing & File Serving:**
- `GET /listing` → HTML directory browser (static folders)
- `GET /listing/{path}` → Browse subdirectories
- `GET /file?path={filepath}` → Serve image file from filesystem

**Scan Operations:**
- `POST /scan` → Start background scan job, returns `job_id`
- `GET /scan-jobs/{job_id}` → Job status
- `GET /scan-jobs/{job_id}/files` → Paginated file results
- `GET /scan-jobs/latest/files` → Latest job results
- `WS /scan-jobs/{job_id}/ws` → Real-time progress via WebSocket

**Image Operations:**
- `GET /api/fetch-image-batch?folder=&page=&size=&sort=` → Paginated images with metadata; includes `already_reviewed` (bool) and `review_rating` (int|null)
- `POST /import` → Import image metadata to DB (no MinIO upload)
- `POST /review` → Full review: saves all DB records + uploads image to MinIO + indexes in Meilisearch

**Search:**
- `GET /api/search?q=&limit=&offset=` → Full-text search via Meilisearch; returns hits with all generation metadata

**Settings:**
- `GET /api/settings` → Returns `{ image_root }` from DB
- `PUT /api/settings` → Updates `{ image_root }` in DB; takes effect immediately on next request

## Data Flow

1. **Scan**: `/scan` → background task walks directory, broadcasts progress via WebSocket
2. **Fetch**: `/api/fetch-image-batch` → reads files, computes sha256, extracts PNG metadata, checks DB for `review_rating`
3. **Review**: `POST /review` with `ReviewDto` → saves Image/Generation/LoRA/Review/Storage/MetaData in one transaction → uploads to MinIO (`ensure_bucket` creates bucket + applies public policy) → indexes in Meilisearch
4. **Search**: `GET /api/search` → queries Meilisearch index → returns hits with full generation metadata including MinIO URL

## Database Models & Relationships

- **Image**: Core entity (width, height, sha256, file path, size, mimetype)
- **Generation**: 1:1 with Image (prompts, cfg, seed, steps, scheduler, model_name)
- **Review**: 1:1 with Image (rating 1–3, comment). Rating values: `1`=very good, `2`=acceptable with flaws, `3`=not acceptable
- **Storage**: 1:1 with Image (MinIO bucket, public URL, sha256 index for deduplication)
- **MetaData**: 1:1 with Image (raw PNG metadata JSON)
- **LoRA**: Many:1 with Generation (model weights, strengths, triggers)
- **Settings**: Single-row config table (image_root)

All models inherit `EntityBaseMixin` (id, created_at, updated_at) and use schema `pony_image`.

## Key Implementation Details

**MinIO bucket management:**
- `ensure_bucket(bucket_name)` creates the bucket if missing, tolerates `BucketAlreadyOwnedByYou`, always applies a public `s3:GetObject` policy
- Public image URLs use port 9000 (S3 API), not 9001 (console)

**Search indexing:**
- `search/indexer.py::build_document()` maps ORM models → Meilisearch document
- `index_review()` errors are caught+logged so a Meilisearch outage doesn't fail the review
- Document `id` = `image.sha256` (unique, meaningful)
- Backfill with `scripts/backfill_search_index.py` for images reviewed before search was added

**Reviewed status in batch response:**
- `get_reviewed_hash_ratings(hashes)` does a single `SELECT sha256, rating FROM storage JOIN image JOIN review WHERE sha256 IN (...)` for the whole page
- Returns `dict[sha256, rating]`; `already_reviewed = hash in result`, `review_rating = result.get(hash)`

**Badge colors in review carousel:**
- Green: rating 1 (very good)
- Yellow: rating 2 (acceptable with flaws)
- Red: rating 3 (not acceptable)

**Settings persistence:**
- `settings_service.get_settings()` seeds the DB row from env var on first call if none exists
- `fetch_image_batch` reads `image_root` from DB on every request — no restart needed after config change

**Alembic autogenerate:**
- Every new model **must** be imported in `alembic/env.py` or autogenerate will produce an empty migration

## Common Development Tasks

**Add a new model field:**
1. Update model in `models/*.py`
2. `cd services/image-importer && .venv/bin/alembic revision --autogenerate -m "description"`
3. Review the generated file — check it's not empty (model must be imported in `alembic/env.py`)
4. `.venv/bin/alembic upgrade head`

**Add a new API endpoint:**
1. Add route to `api/app.py`
2. Add DTOs in `dto/`
3. Add service logic in `services/`
4. Add tests in `tests/`
5. Update frontend in `image-review/src/routes/`

**Add a new settings field:**
1. Add column to `models/settings.py`
2. Run migration
3. Update `services/settings_service.py`
4. Add to `SettingsDto` in `dto/response/response_dto.py`
5. Update `GET/PUT /api/settings` in `api/app.py`
6. Update `config/+page.svelte`

**Add a new frontend page:**
- Create `src/routes/<name>/+page.svelte`
- Add nav entry in `src/routes/+layout.svelte`
- Add e2e tests in `e2e/<name>.spec.ts`

## Debugging Tips

- **Backend logs**: Watch uvicorn output; also check `reports/test-report.html` after test runs
- **WebSocket**: Browser DevTools → Network → WS tab
- **Database**: `psql postgresql://pony_admin:admin@localhost:5432/pony`
- **MinIO**: Web UI at http://localhost:9001 (admin / 12345678)
- **Meilisearch**: http://localhost:7700 (master key: `meili@goe-nostromo-04`)
- **Search not returning results**: Run backfill script; check Meilisearch is running

## Notes

- SHA256 uniqueness enforced at DB level — duplicate imports return a clean error, not a crash
- ComfyUI prompt structure varies; `excerpt_parser` handles missing nodes gracefully
- Frontend uses SvelteKit runes (Svelte 5); older Svelte syntax not supported
- E2e tests mock `page.route()` for API calls — no live backend needed for most specs
