#!/bin/bash
# reset_migrations.sh
psql postgresql://pony_admin:admin@localhost:5432/pony -c "
    DROP TABLE IF EXISTS pony_image.lora_image CASCADE;
    DROP TABLE IF EXISTS pony_image.lora CASCADE;
    DROP TABLE IF EXISTS pony_image.generation CASCADE;
    DROP TABLE IF EXISTS pony_image.meta_data CASCADE;
    DROP TABLE IF EXISTS pony_image.review CASCADE;
    DROP TABLE IF EXISTS pony_image.storage CASCADE;
    DROP TABLE IF EXISTS pony_image.workflow CASCADE;
    DROP TABLE IF EXISTS pony_image.image CASCADE;
    DROP TABLE IF EXISTS pony_image.alembic_version CASCADE;
"
rm -f alembic/versions/*.py
alembic revision --autogenerate -m "initial schema"
alembic upgrade head