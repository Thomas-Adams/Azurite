create table pony_image.image_assets (
   id bigserial primary key,

   filename text not null,
   path text not null,
   width int not null check (width > 0),
   height int not null check (height > 0),
   mimetype varchar(50) not null,
   filesize_bytes bigint,
   sha256 char(64) not null,

   workflow jsonb,
   sidecar_json jsonb,

   positive_prompt text,
   negative_prompt text,
   seed bigint,
   steps int,
   cfg numeric(8,3),
   sampler text,
   scheduler text,
   model_name text,
   loras jsonb,
   generation_params jsonb,

   quality_rating smallint not null default 0,
   quality_comment text,
   reviewed_at timestamptz,

   created_at timestamptz not null default current_timestamp,
   modified_at timestamptz,
   imported_at timestamptz not null default current_timestamp,

   constraint image_assets_path_unique unique (path),
   constraint image_assets_sha256_unique unique (sha256),
   constraint image_assets_quality_rating_chk check (quality_rating between 0 and 5)
);

grant select on pony_image.image_assets to pony_anon;

-- logged-in read-only
grant select on pony_image.image_assets to pony_webuser;

-- editor (full data access)
grant select, insert, update, delete
    on pony_image.image_assets
    to pony_editor;

-- admin (everything)
grant all privileges on pony_image.image_assets to pony_admin;


grant usage, select on sequence pony_image.image_assets_id_seq
    to pony_editor;

grant usage, select on sequence pony_image.image_assets_id_seq
    to pony_webuser;

grant usage, select on sequence pony_image.image_assets_id_seq
    to pony_anon;

grant all on sequence pony_image.image_assets_id_seq
    to pony_admin;