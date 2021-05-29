-- drop table if exists cards;
create table cards (
  id integer primary key autoincrement,
  type tinyint not null, /* 1 for vocab, 2 for code */
  front text not null,
  back text not null,
  known boolean default 0
);

create table tags (
  id integer primary key autoincrement,
  tagName text not null
);
