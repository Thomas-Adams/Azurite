# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Azurite** is a full-stack image review and management system for AI-generated images (primarily from Stable Diffusion). It consists of:

- **Backend**: FastAPI-based image importer service with PostgreSQL database and MinIO object storage
- **Frontend**: SvelteKit web application with Tailwind CSS for reviewing and browsing generated images

The system captures image metadata from ComfyUI workflows, stores generation parameters, and provides an interface for rating and reviewing images.

## Repository Structure

```
Azurite/
├── image-review/          # SvelteKit frontend application
│   ├── src/
│   │   ├── routes/        # SvelteKit pages (+page.svelte, +layout.svelte)
│   │   │   ├── +page.svelte (home)
│   │   │   └── view/+page.svelte (image browser/review interface)
│   │   ├── lib/
│   │   │   ├── components/custom/ (ReviewDialog, ReviewNavigationBar, ui-types)
│   │   │   └── components/ui/ (skeleton UI library dialogs)
│   │   └── app.html
│   ├── package.json, pnpm-workspace.yaml, tsconfig.json
│   ├── vite.config.ts, svelte.config.js, tailwindcss.config.js
│   └── .svelte-kit/ (generated)
│
├── services/image-importer/  # FastAPI backend service
│   ├── api/
│   │   ├── app.py (main routes: /listing, /file, /scan, /import, /api/fetch-image-batch, /api/review)
│   │   ├── state.py (FastAPI app config, static folders, constants)
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
│   │   ├── storage.py (Storage: MinIO bucket info)
│   │   ├── meta_data.py (MetaData: raw PNG metadata JSON)
│   │   └── workflow.py
│   ├── services/
│   │   └── image_importer.py (core logic: metadata parsing, image import, DB operations)
│   ├── utils/
│   │   ├── image_sha.py (sha256 hashing)
│   │   ├── image_utils.py (image dimension reading)
│   │   └── excerpt_parser.py (ComfyUI metadata extraction)
│   ├── database/ (AsyncSession factory, engine setup)
│   ├── config/ (Settings via Pydantic)
│   ├── minio/ (MinIO client config)
│   ├── dto/ (request/response DTOs)
│   ├── alembic/ (database migrations)
│   ├── requirements.txt (dependencies)
│   └── alembic.ini, reset_migrations.sh
│
├── database/ (root-level database scripts)
└── .venv/ (Python virtual environment)
```

## Key Technologies

**Frontend:**
- Svelte 5 (runes mode) with SvelteKit
- Tailwind CSS 4 with typography and forms plugins
- `lib/components/ui/` — shadcn-svelte components, managed via `jsrepo` (`@ieedan/shadcn-svelte-extras` registry); Bits UI is the headless primitive underneath
- `lib/components/custom/` — hand-written components that import directly from `@skeletonlabs/skeleton-svelte` (Dialog, Carousel, Pagination, Navigation)
- TypeScript 6

**Backend:**
- FastAPI 0.135+ with Uvicorn
- SQLAlchemy 2 async ORM with PostgreSQL (asyncpg)
- Alembic for database migrations
- MinIO 7 for object storage
- Pydantic 2 for validation

**Database:**
- PostgreSQL with schema: `pony_image`
- Tables: image, generation, lora, review, storage, meta_data, workflow, lora_image
- Unique constraint on image.sha256
- Check constraints on image width/height > 0

## Development Setup

### Backend (Python)

1. **Virtual environment**: Already set up at `.venv/`
   ```bash
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r services/image-importer/requirements.txt
   ```

3. **Database setup**:
   - PostgreSQL running on localhost:5432
   - Database: `pony` (or set `AZURITE_DB_NAME`)
   - Schema: `pony_image`
   - User: `pony_admin` / password: `admin` (configurable via `AZURITE_DB_*` env vars)
   - Run migrations: `cd services/image-importer && alembic upgrade head`
   - Reset migrations (destructive): `bash reset_migrations.sh`

4. **MinIO setup**:
   - MinIO instance on localhost:9000
   - Configured in `services/image-importer/minio/config.py`

5. **Environment variables** (in `.env` or prefix with `AZURITE_`):
   ```
   AZURITE_IMAGE_ROOT=/home/tadams/stable-diffusion
   AZURITE_DB_HOST=localhost
   AZURITE_DB_PORT=5432
   AZURITE_DB_NAME=pony
   AZURITE_DB_USER=pony_admin
   AZURITE_DB_PASSWORD=admin
   AZURITE_DB_SCHEMA=pony_image
   AZURITE_DEBUG=true
   ```

6. **Run API server**:
   ```bash
   cd services/image-importer
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend (Node/pnpm)

1. **Install dependencies**:
   ```bash
   cd image-review
   pnpm install
   ```

2. **Run development server**:
   ```bash
   pnpm dev
   # Opens on http://localhost:5173
   ```

3. **Build production**:
   ```bash
   pnpm build
   ```

4. **Type check**:
   ```bash
   pnpm check
   pnpm check:watch  # Watch mode
   ```

5. **CORS**: Frontend (http://localhost:5173) is whitelisted in backend's `api/state.py`

## API Routes

**Image Listing & File Serving:**
- `GET /listing` → HTML directory browser
- `GET /listing/{path}` → Browse subdirectories
- `GET /file?path={filepath}` → Serve image file

**Scan Operations:**
- `POST /scan` → Initiate background scan job, returns `job_id`
- `GET /scan-jobs/{job_id}` → Get job status
- `GET /scan-jobs/{job_id}/files` → Paginated results (offset, limit)
- `GET /scan-jobs/latest/files` → Latest job results
- `WS /scan-jobs/{job_id}/ws` → WebSocket for real-time progress updates

**Image Operations:**
- `GET /api/fetch-image-batch?folder={folder}&page={page}&size={size}&sort={sort}` → Paginated image batch with metadata (sha256, dimensions, size, etc.)
- `POST /import` → Import image metadata to database (bulk operation)
- `POST /api/review` → **stub, not yet implemented** (`pass`)

## Data Flow

1. **Scan**: User initiates `/scan` with folder path → background task walks directory, collects matching files, broadcasts progress via WebSocket
2. **Fetch**: Frontend requests `/api/fetch-image-batch` → reads files, computes sha256, extracts PNG metadata or JSON sidecar
3. **Import (metadata-only path)**: POST `/import` → `read_png_metadata()` or `read_png_sidecar()` → `import_one()` creates Image, Generation, LoRA, Review, Storage, MetaData records in one transaction; no MinIO upload
4. **Import (full upload path)**: `upload_and_review_image()` — called with a `ReviewDto` — reads image, saves all DB records, then uploads to MinIO bucket; returns all created models

## Database Models & Relationships

- **Image**: Core entity (width, height, sha256, file path, size, mimetype)
- **Generation**: 1:1 with Image (prompts, cfg, seed, steps, scheduler, model_name)
- **Review**: 1:1 with Image (rating, comment)
- **Storage**: 1:1 with Image (MinIO bucket, URL, file info for cloud storage)
- **MetaData**: 1:1 with Image (raw PNG metadata JSON)
- **LoRA**: Many:1 with Generation (model weights, strengths, triggers)

All models inherit from `EntityBaseMixin` (id, created_at, updated_at) and use schema `pony_image`.

## Key Implementation Details

**Metadata Extraction:**
- PNG files: Read embedded `workflow` and `prompt` from PIL Image.info
- Fallback: Look for `.json` sidecar file next to image
- `excerpt_parser.extract_comfyui_essentials()` parses ComfyUI node structure to extract loras, positive/negative prompts, steps, cfg, etc.

**Image Processing:**
- `image_metadata()` returns dict with raw PNG info, workflow, parsed prompt, sidecar data
- `image_utils.read_image_size()` gets width/height
- `image_sha.sha256_of_file()` computes file hash for deduplication

**Async Pattern:**
- `async_session_factory()` provides AsyncSession for each operation
- All DB operations within try/except with rollback on error
- Background tasks use `BackgroundTasks` for non-blocking operations

**Image Serving:**
- `IMAGE_ROOT` configured in env (defaults to `/home/tadams/stable-diffusion`)
- `STATIC_FOLDERS` mounted separately for security (prevents path traversal)
- `/file` endpoint validates extension and path before serving

**Frontend Integration:**
- ReviewDialog modal for image rating/comments
- ReviewNavigationBar for pagination
- Pagination via query params: `page`, `size`, `sort`
- Sort options: `name`, `size`, `date`

## Common Development Tasks

**Add a new image metadata field:**
1. Update `Image` or `Generation` model in `models/*.py`
2. Extract in `extract_comfyui_essentials()` if from ComfyUI data
3. Update `import_one()` to populate the field
4. Run migration: `alembic revision --autogenerate -m "add field"`
5. Apply: `alembic upgrade head`

**Add a new API endpoint:**
1. Create route in `services/image-importer/api/app.py`
2. Define request/response DTOs in `dto/`
3. Call service functions from `services/image_importer.py`
4. Update frontend in `image-review/src/routes/` if user-facing

**Frontend page development:**
- Use `+page.svelte` in `src/routes/` directory
- Import API client from `lib/` and call backend routes
- Use Skeleton UI components from `lib/components/ui/`
- Style with Tailwind utility classes

**Database migration:**
- Edit model, then: `alembic revision --autogenerate -m "description"`
- Review generated file in `alembic/versions/`
- Apply: `alembic upgrade head`

**Testing database changes:**
- Run `reset_migrations.sh` to drop tables and regenerate migrations (DEV ONLY)
- This will prompt Alembic to create a fresh schema

## Debugging Tips

- **Backend logs**: Watch uvicorn output for request traces and errors
- **WebSocket progress**: Check browser DevTools → Network → WS tab for real-time updates
- **Database issues**: `psql postgresql://pony_admin:admin@localhost:5432/pony` to query directly
- **Image metadata**: Use `image_importer.image_metadata(Path("..."))` to test extraction
- **MinIO**: Access web UI at http://localhost:9001 (default creds: minioadmin/minioadmin)

## Notes

- Image filenames stored with full path to enable browsing nested folders
- SHA256 uniqueness enforced at DB level to prevent duplicate imports
- Aspect ratio calculated only if height > 0 (avoids division by zero)
- ComfyUI prompt structure varies; `excerpt_parser` handles missing nodes gracefully
- Frontend uses SvelteKit runes (Svelte 5) for reactivity; older Svelte syntax not supported
