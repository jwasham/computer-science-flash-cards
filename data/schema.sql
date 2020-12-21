drop table if exists cards;
drop table if exists tag;
drop table if exists cards_tag;

create table cards (
    id integer primary key autoincrement,
    type tinyint not null, /* 1 for vocab, 2 for code */
    front text not null,
    back text not null,
    known boolean default 0
);

create table tag (
    id integer primary key autoincrement,
    tag_name text not null
);

create table cards_tag (
    cards_id integer not null,
    tag_id integer not null,
    foreign key (cards_id) references cards(id),
    foreign key (tag_id) references tag(id),
    primary key(cards_id, tag_id)
);

