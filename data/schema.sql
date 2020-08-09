drop table if exists cards;
create table cards (
  id integer primary key autoincrement,
  type tinyint not null, /* 1 for vocab, 2 for code */
  front text not null,
  back text not null,
  known boolean default 0
);

drop table if exists card_types;
CREATE TABLE "card_types" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"card_name"	TEXT
);

DROP TABLE IF EXISTS card_multiple_choice;
CREATE TABLE "card_multiple_choices" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "card_id" INTEGER,
  "card_choice" TEXT NOT NULL,
  "correct_choice" BOOLEAN DEFAULT 0,
  FOREIGN KEY (card_id) REFERENCES cards(id)
);
