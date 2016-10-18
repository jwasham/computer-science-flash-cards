#!/bin/bash

export CARDS_SETTINGS=/src/config.txt
gunicorn --bind  0.0.0.0:8000 flash_cards:app