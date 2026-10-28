-- demo_data: true (synthetic fixture: must FAIL the RLS check)
create table public.profiles (
  id uuid primary key references auth.users(id),
  email text
);

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references auth.users(id),
  name text
);

alter table public.projects enable row level security;

-- Trivial policy: every row is readable and writable by anyone.
create policy "anyone can do anything"
  on public.projects for all
  using (true)
  with check (true);
