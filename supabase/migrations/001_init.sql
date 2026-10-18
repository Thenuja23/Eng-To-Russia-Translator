-- Core tables per data model
create table if not exists profiles (
  id uuid primary key,
  role text check (role in ('student','admin')) default 'student',
  target_language text default 'en',
  consent_training_use boolean default false,
  created_at timestamp with time zone default now()
);

create table if not exists uploaded_images (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  input_type text,
  raw_text text,
  ocr_mode text,
  direction text,
  preferred_cursive_style text,
  feedback_status text,
  created_at timestamp with time zone default now()
);

create table if not exists ocr_results (
  id uuid primary key default gen_random_uuid(),
  image_id uuid references uploaded_images(id),
  lines jsonb,
  source_method text,
  latency_ms integer,
  created_at timestamp with time zone default now()
);

create table if not exists translations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  source_text text,
  translated_text text,
  engine text,
  created_at timestamp with time zone default now()
);

create table if not exists user_corrections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  line_id uuid,
  corrected_text text,
  review_status text,
  used_in_training boolean default false,
  created_at timestamp with time zone default now()
);
