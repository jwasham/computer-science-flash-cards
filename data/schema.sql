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

DROP TABLE IF EXISTS card_multiple_choices;
CREATE TABLE "card_multiple_choices" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "card_id" INTEGER,
  "card_choice" TEXT NOT NULL,
  "correct_choice" BOOLEAN DEFAULT 0,
  FOREIGN KEY (card_id) REFERENCES cards(id)
);

-- Represents a test for a given category
-- There can be multiple tests for a given category
-- Currently a test can only be composed of cards from 1 category
DROP TABLE IF EXISTS test_multiple_choice;
CREATE TABLE "test_multiple_choice" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "card_type_id" INTEGER,
  "created_time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
  FOREIGN KEY (card_type_id) REFERENCES card_types(id)
)

-- Represents the cards for a multiple choice test
-- There are expected to be more than 1 questions for a test
DROP TABLE IF EXISTS test_multiple_choice_cards;
CREATE TABLE "test_multiple_choice_cards" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "test_multiple_choice_id" INTEGER,
  "card_id" INTEGER,
  FOREIGN KEY (card_id) REFERENCES cards(id),
  FOREIGN KEY (test_multiple_choice_id) REFERENCES test_multiple_choice(id)
)

-- Represents the order of the multiple choices when presented
-- to the end user in a test
DROP TABLE IF EXISTS test_multiple_choice_questions_order;
CREATE TABLE "test_multiple_choice_questions_order" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "position" INTEGER NOT NULL,
  "test_multiple_choice_card_id" INTEGER NOT NULL,
  "card_multiple_choice_id" INTEGER,
  FOREIGN KEY (test_multiple_choice_card_id) REFERENCES test_multiple_choice_cards(id),
  FOREIGN KEY (card_multiple_choice_id) REFERENCES card_multiple_choices(id)
)

-- Represents the answers given to a multiple choice test
DROP TABLE IF EXISTS test_multiple_choice_answers;
CREATE TABLE "test_multiple_choice_answers" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "created_time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "test_multiple_choice_id" INTEGER,
  "card_id" INTEGER,
  "answer" INTEGER,
  "correct_answer" INTEGER,
  FOREIGN KEY (test_multiple_choice_id) REFERENCES test_multiple_choice(id),
  FOREIGN KEY (answer) REFERENCES card_multiple_choices(id),
  FOREIGN KEY (card_id) REFERENCES cards(id)
)

-- Represents the results from a test
DROP TABLE IF EXISTS test_multiple_choice_results;
CREATE TABLE "test_multiple_choice_results" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "created_time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
  "test_multiple_choice_id" INTEGER,
  "total_correct" INTEGER NOT NULL,
  "total_incorrect" INTEGER NOT NULL,
  "percentage" REAL NOT NULL,
  FOREIGN KEY (test_multiple_choice_id) REFERENCES test_multiple_choice(id)
)
