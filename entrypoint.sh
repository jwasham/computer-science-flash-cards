#!/bin/bash

if [ ! -f /src/db/cards.db ]; then
	mkdir -p /src/db
	cp cards-jwasham.db /src/db/cards.db
fi

export CARDS_SETTINGS=/src/config.txt
gunicorn --bind  0.0.0.0:8000 flash_cards:app