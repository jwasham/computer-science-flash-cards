# Computer Science Flash Cards

This is a little website I've put together to allow me to easily make flash cards and quiz myself for memorization of:

- general cs knowledge
    - vocabulary
    - definitions of processes
    - powers of 2
    - design patterns
- code
    - data structures
    - algorithms
    - solving problems
    - bitwise operations

Will be able to use it on:
    - desktop
    - mobile (phone and tablet)

It uses:
- Python 3
- Flask
- SQLite

---

## How to run it

1. Clone project to a directory on your web server.
1. Edit the config.txt file. The username and password will be the login
    for your site. There is only one user - you.
1. Follow this long tutorial to get Flask running. It was way more work than it should be:
    https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-16-04
    - `wsgy.py` is the entry point. It calls `flash_cards.py`
    - This is my systemd file `/etc/systemd/system/flash_cards.service`: [view](flash_cards.service)
        - you can see the paths where I installed it, and the name of my virtualenv directory
    - when done with tutorial:
    ```
    sudo systemctl restart flash_cards
    sudo systemctl daemon-reload
    ```
1. When you see a login page, you're good to go.
1. Uncomment the commented block in `flash_cards.py`
1. Restart Flask. You have to use `sudo systemctl restart flash_cards`.
1. Hit the URL /initdb on your web server. You'll see a message that the
    database has been initialized.
1. Comment that code again.
1. Restart Flask.
1. Go to / on your webserver.
1. Log in.
1. Click the "General" or "Code" button and make a card!
1. When you're ready to start memorizing, click either "General" or "Code"
    in the top menu.

*Happy learning!*