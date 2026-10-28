-- demo_data: true (synthetic fixture for the quality gate)
create table public.projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id),
  name text not null
);

alter table public.projects enable row level security;

create policy "owners read their projects"
  on public.projects for select
  using (auth.uid() = owner_id);

create policy "owners write their projects"
  on public.projects for all
  using (auth.uid() = owner_id)
  with check (auth.uid() = owner_id);
