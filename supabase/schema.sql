create table if not exists change_orders (
  id text primary key,
  owner_token text not null unique,
  contractor_name text not null,
  contractor_email text not null,
  client_name text not null,
  title text not null,
  description text not null,
  timeline_impact text not null default 'No impact specified',
  amount_cents integer not null,
  currency text not null,
  status text not null default 'pending' check (status in ('pending', 'approved', 'declined')),
  created_at timestamptz not null,
  decided_at timestamptz,
  approver_name text,
  approver_email text
);

create table if not exists events (
  id bigserial primary key,
  change_order_id text not null references change_orders(id),
  event_type text not null,
  occurred_at timestamptz not null,
  user_agent text
);

alter table change_orders enable row level security;
alter table events enable row level security;

-- The app connects with the server-side Postgres connection string. Do not expose it to browsers.
