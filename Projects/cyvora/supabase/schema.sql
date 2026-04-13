create extension if not exists "pgcrypto";

create table if not exists public.companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  phone text,
  trial_started_at timestamptz not null default timezone('utc', now()),
  trial_ends_at timestamptz not null default (timezone('utc', now()) + interval '10 days'),
  billing_status text not null default 'trial_active',
  plan text not null default 'trial',
  retell_agent_id text,
  retell_llm_id text,
  retell_base_general_prompt text,
  first_number_assigned_at timestamptz,
  trial_reminder_sent_at timestamptz,
  trial_expired_email_sent_at timestamptz,
  stripe_customer_id text,
  stripe_subscription_id text,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  company_id uuid references public.companies (id) on delete set null,
  email text not null,
  full_name text,
  phone text,
  role text not null default 'owner',
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.calls (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  external_call_id text not null unique,
  assistant_id text,
  customer_number text,
  started_at timestamptz,
  ended_at timestamptz,
  duration_seconds integer,
  status text,
  ended_reason text,
  summary text,
  transcript text,
  recording_url text,
  urgency text,
  booking_status text,
  raw_payload jsonb,
  structured_data jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.appointments (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  call_id uuid references public.calls (id) on delete set null,
  external_call_id text unique,
  contact_phone text,
  scheduled_for timestamptz,
  status text not null default 'confirmed',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  stripe_customer_id text,
  stripe_subscription_id text not null unique,
  stripe_price_id text,
  status text not null default 'active',
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.vapi_phone_numbers (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade unique,
  vapi_phone_number_id text not null unique,
  vapi_assistant_id text,
  phone_number text not null,
  label text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.retell_phone_assignments (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade unique,
  phone_number text not null unique,
  phone_number_pretty text,
  nickname text,
  inbound_agent_id text,
  outbound_agent_id text,
  phone_number_type text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

alter table public.companies add column if not exists billing_status text not null default 'trial_active';
alter table public.companies add column if not exists plan text not null default 'trial';
alter table public.companies add column if not exists retell_agent_id text;
alter table public.companies add column if not exists retell_llm_id text;
alter table public.companies add column if not exists retell_base_general_prompt text;
alter table public.companies add column if not exists first_number_assigned_at timestamptz;
alter table public.companies add column if not exists trial_reminder_sent_at timestamptz;
alter table public.companies add column if not exists trial_expired_email_sent_at timestamptz;
alter table public.companies add column if not exists stripe_customer_id text;
alter table public.companies add column if not exists stripe_subscription_id text;

alter table public.companies enable row level security;
alter table public.profiles enable row level security;
alter table public.calls enable row level security;
alter table public.appointments enable row level security;
alter table public.subscriptions enable row level security;
alter table public.vapi_phone_numbers enable row level security;
alter table public.retell_phone_assignments enable row level security;

drop policy if exists "Users can read their own profile" on public.profiles;
create policy "Users can read their own profile"
on public.profiles
for select
to authenticated
using (auth.uid() = id);

drop policy if exists "Users can update their own profile" on public.profiles;
create policy "Users can update their own profile"
on public.profiles
for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);

drop policy if exists "Users can insert their own profile" on public.profiles;
create policy "Users can insert their own profile"
on public.profiles
for insert
to authenticated
with check (auth.uid() = id);

drop policy if exists "Users can insert their own company" on public.companies;
create policy "Users can insert their own company"
on public.companies
for insert
to authenticated
with check (true);

drop policy if exists "Users can read their company" on public.companies;
create policy "Users can read their company"
on public.companies
for select
to authenticated
using (
  exists (
    select 1
    from public.profiles
    where public.profiles.company_id = companies.id
      and public.profiles.id = auth.uid()
  )
);

drop policy if exists "Users can read company calls" on public.calls;
create policy "Users can read company calls"
on public.calls
for select
to authenticated
using (
  exists (
    select 1
    from public.profiles
    where public.profiles.company_id = calls.company_id
      and public.profiles.id = auth.uid()
  )
);

drop policy if exists "Users can read company appointments" on public.appointments;
create policy "Users can read company appointments"
on public.appointments
for select
to authenticated
using (
  exists (
    select 1
    from public.profiles
    where public.profiles.company_id = appointments.company_id
      and public.profiles.id = auth.uid()
  )
);

drop policy if exists "Users can read company subscriptions" on public.subscriptions;
create policy "Users can read company subscriptions"
on public.subscriptions
for select
to authenticated
using (
  exists (
    select 1
    from public.profiles
    where public.profiles.company_id = subscriptions.company_id
      and public.profiles.id = auth.uid()
  )
);

drop policy if exists "Users can read company vapi phone numbers" on public.vapi_phone_numbers;
create policy "Users can read company vapi phone numbers"
on public.vapi_phone_numbers
for select
to authenticated
using (
  exists (
    select 1
    from public.profiles
    where public.profiles.company_id = vapi_phone_numbers.company_id
      and public.profiles.id = auth.uid()
  )
);

drop policy if exists "Users can read company retell phone assignments" on public.retell_phone_assignments;
create policy "Users can read company retell phone assignments"
on public.retell_phone_assignments
for select
to authenticated
using (
  exists (
    select 1
    from public.profiles
    where public.profiles.company_id = retell_phone_assignments.company_id
      and public.profiles.id = auth.uid()
  )
);

drop trigger if exists set_calls_updated_at on public.calls;
drop trigger if exists set_appointments_updated_at on public.appointments;
drop trigger if exists set_subscriptions_updated_at on public.subscriptions;
drop trigger if exists set_vapi_phone_numbers_updated_at on public.vapi_phone_numbers;
drop trigger if exists set_retell_phone_assignments_updated_at on public.retell_phone_assignments;

drop function if exists public.set_updated_at();
create function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create trigger set_calls_updated_at
before update on public.calls
for each row execute procedure public.set_updated_at();

create trigger set_appointments_updated_at
before update on public.appointments
for each row execute procedure public.set_updated_at();

create trigger set_subscriptions_updated_at
before update on public.subscriptions
for each row execute procedure public.set_updated_at();

create trigger set_vapi_phone_numbers_updated_at
before update on public.vapi_phone_numbers
for each row execute procedure public.set_updated_at();

create trigger set_retell_phone_assignments_updated_at
before update on public.retell_phone_assignments
for each row execute procedure public.set_updated_at();

drop trigger if exists on_auth_user_created on auth.users;

drop function if exists public.handle_new_user();
create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  new_company_id uuid;
  company_name text;
  company_phone text;
begin
  company_name := coalesce(
    new.raw_user_meta_data->>'company_name',
    new.raw_user_meta_data->>'full_name',
    split_part(new.email, '@', 1)
  );

  company_phone := new.raw_user_meta_data->>'phone';

  insert into public.companies (name, phone)
  values (company_name, company_phone)
  returning id into new_company_id;

  insert into public.profiles (id, company_id, email, full_name, phone)
  values (
    new.id,
    new_company_id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', company_name),
    company_phone
  )
  on conflict (id) do update
  set
    company_id = excluded.company_id,
    email = excluded.email,
    full_name = excluded.full_name,
    phone = excluded.phone;

  return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();
