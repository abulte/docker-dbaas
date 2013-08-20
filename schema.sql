drop table if exists databases;
create table databases (
  id integer primary key autoincrement,
  docker_id integer not null,
  name text not null,
  type text not null,
  port_mapping boolean default true,
  memory_limit integer default 0
);