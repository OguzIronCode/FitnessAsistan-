-- =====================================================
-- FitTrack AI — Supabase SQL Şeması
-- Supabase Dashboard → SQL Editor'a yapıştır ve çalıştır
-- =====================================================

-- UUID extension (genellikle aktif gelir)
create extension if not exists "uuid-ossp";

-- ─── Profiles ─────────────────────────────────────────────────────────────────
create table if not exists profiles (
  id                  uuid primary key references auth.users(id) on delete cascade,
  full_name           text not null,
  gender              text check (gender in ('male','female','other')),
  age                 integer,
  height_cm           numeric,
  weight_kg           numeric,
  goal                text check (goal in ('cut','bulk','maintain')),
  activity_level      text default 'moderate',
  weekly_workout_days integer default 4,
  diet_preference     text default 'balanced',
  calorie_target      integer,
  protein_target      integer,
  carb_target         integer,
  fat_target          integer,
  created_at          timestamptz default now(),
  updated_at          timestamptz default now()
);

-- ─── Foods (CSV'den) ──────────────────────────────────────────────────────────
create table if not exists foods (
  id              bigserial primary key,
  name            text,
  name_tr         text,
  serving_size    text default '100 g',
  calories        numeric,
  protein         numeric,
  carbohydrate    numeric,
  fat             numeric,
  fiber           numeric,
  sugars          numeric,
  sodium          numeric,
  potassium       numeric,
  calcium         numeric,
  iron            numeric,
  vitamin_c       numeric,
  vitamin_a       numeric
);

create index if not exists foods_name_tr_idx on foods using gin (to_tsvector('simple', coalesce(name_tr, '')));
create index if not exists foods_name_idx    on foods using gin (to_tsvector('simple', coalesce(name, '')));

-- ─── Supplements (CSV'den) ────────────────────────────────────────────────────
create table if not exists supplements (
  id                    bigserial primary key,
  brand_name            text,
  product_name          text,
  product_category      text,
  product_description   text,
  price                 numeric,
  price_per_serving     numeric,
  overall_rating        numeric,
  average_flavor_rating numeric,
  number_of_reviews     integer,
  top_flavor_rated      text,
  link                  text
);

-- ─── Programs (CSV'den) ───────────────────────────────────────────────────────
create table if not exists programs (
  id                uuid primary key default uuid_generate_v4(),
  title             text not null,
  description       text,
  level             text,
  goal              text,
  equipment         text,
  program_length    text,
  time_per_workout  text,
  total_exercises   integer
);

-- ─── Meals ────────────────────────────────────────────────────────────────────
create table if not exists meals (
  id        uuid primary key default uuid_generate_v4(),
  user_id   uuid references auth.users(id) on delete cascade,
  date      date not null,
  meal_type text check (meal_type in ('breakfast','lunch','dinner','snack')),
  food_id   bigint references foods(id),
  amount_g  numeric not null,
  calories  numeric default 0,
  protein   numeric default 0,
  carb      numeric default 0,
  fat       numeric default 0,
  created_at timestamptz default now()
);

create index if not exists meals_user_date_idx on meals(user_id, date);

-- ─── Workouts ────────────────────────────────────────────────────────────────
create table if not exists workouts (
  id           uuid primary key default uuid_generate_v4(),
  user_id      uuid references auth.users(id) on delete cascade,
  program_id   uuid references programs(id),
  date         date not null,
  duration_min integer,
  total_sets   integer default 0,
  notes        text,
  created_at   timestamptz default now()
);

create index if not exists workouts_user_date_idx on workouts(user_id, date);

-- ─── Workout Sets ─────────────────────────────────────────────────────────────
create table if not exists workout_sets (
  id             uuid primary key default uuid_generate_v4(),
  workout_id     uuid references workouts(id) on delete cascade,
  exercise_name  text not null,
  set_number     integer not null,
  reps           integer,
  weight_kg      numeric,
  completed      boolean default true,
  created_at     timestamptz default now()
);

-- ─── Body Metrics ────────────────────────────────────────────────────────────
create table if not exists body_metrics (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references auth.users(id) on delete cascade,
  date          date not null,
  weight_kg     numeric,
  body_fat_pct  numeric,
  muscle_pct    numeric,
  waist_cm      numeric,
  created_at    timestamptz default now(),
  unique (user_id, date)
);

-- ─── RLS Politikaları ─────────────────────────────────────────────────────────
alter table profiles     enable row level security;
alter table meals        enable row level security;
alter table workouts     enable row level security;
alter table workout_sets enable row level security;
alter table body_metrics enable row level security;

-- Profiles: sadece kendi profilini gör/düzenle
create policy "Profiles: own" on profiles
  using (auth.uid() = id) with check (auth.uid() = id);

-- Meals: sadece kendi öğünleri
create policy "Meals: own" on meals
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Workouts: sadece kendi antrenmanları
create policy "Workouts: own" on workouts
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Workout sets: antrenman sahibi erişebilir
create policy "Sets: workout owner" on workout_sets
  using (
    exists (
      select 1 from workouts w
      where w.id = workout_sets.workout_id
        and w.user_id = auth.uid()
    )
  );

-- Body metrics: sadece kendi
create policy "Body metrics: own" on body_metrics
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Foods, supplements, programs herkese açık (okuma)
create policy "Foods: read" on foods for select using (true);
create policy "Supplements: read" on supplements for select using (true);
create policy "Programs: read" on programs for select using (true);

alter table foods        enable row level security;
alter table supplements  enable row level security;
alter table programs     enable row level security;

-- ─── Migration: meals tablosuna image_url ekle ───────────────────────────────
-- Supabase SQL Editor'da bir kez çalıştır:
alter table meals add column if not exists image_url text;

-- ─── Helper Function: total_sets artır ───────────────────────────────────────
create or replace function increment_total_sets(wid uuid)
returns void language sql as $$
  update workouts set total_sets = total_sets + 1 where id = wid;
$$;

-- ─── Profil updated_at trigger ────────────────────────────────────────────────
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger profiles_updated_at
  before update on profiles
  for each row execute function update_updated_at();
