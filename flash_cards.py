import os
import sqlite3
from collections import namedtuple
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'db', 'cards.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='ftd0000'
))
app.config.from_envvar('CARDS_SETTINGS', silent=True)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    db = get_db()
    with app.open_resource('data/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# -----------------------------------------------------------

# Uncomment and use this to initialize database, then comment it
#   You can rerun it to pave the database and start over
@app.route('/initdb')
def initdb():
    db_path = os.path.join('db', 'cards.db')
    if os.path.exists(db_path):
        return 'db exists.'
    init_db()
    return 'Initialized the database.'


@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('general'))
    else:
        return redirect(url_for('login'))


@app.route('/cards')
def cards():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with get_db() as db:
        cards_query = '''
            SELECT id, type, front, back, known
            FROM cards
            ORDER BY id DESC
        '''
        cur = db.execute(cards_query)
        cards_data = cur.fetchall()

        cards = []

        Card = namedtuple('Card', ['id', 'type', 'front', 'back', 'known', 'tags'])
        for card_data in cards_data:
            card_tags_query = '''
                SELECT t.tag_name
                FROM tag t JOIN cards_tag ct ON ct.tag_id = t.id
                WHERE ct.cards_id = ?
            '''
            cur = db.execute(card_tags_query, [card_data['id']])
            tags_data = cur.fetchall()
            card_tags = [t['tag_name'] for t in tags_data]
            card = Card(
                card_data['id'],
                card_data['type'],
                card_data['front'],
                card_data['back'],
                card_data['known'],
                card_tags)
            cards.append(card)

        tags_query = '''
            SELECT id, tag_name
            FROM tag
            ORDER BY id DESC
        '''

        cur = db.execute(tags_query)
        tags = cur.fetchall()

    return render_template('cards.html', cards=cards, tags=tags, filter_name="all")


@app.route('/filter_cards/<filter_name>')
def filter_cards(filter_name):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filters = {
        "all":      "where 1 = 1",
        "general":  "where type = 1",
        "code":     "where type = 2",
        "known":    "where known = 1",
        "unknown":  "where known = 0",
    }

    query = filters.get(filter_name)

    if not query:
        return redirect(url_for('cards'))

    with get_db() as db:
        fullquery = "SELECT id, type, front, back, known FROM cards " + query + " ORDER BY id DESC"
        cur = db.execute(fullquery)
        cards_data = cur.fetchall()

        cards = []

        Card = namedtuple('Card', ['id', 'type', 'front', 'back', 'known', 'tags'])
        for card_data in cards_data:
            card_tags_query = '''
                SELECT t.tag_name
                FROM tag t JOIN cards_tag ct ON ct.tag_id = t.id
                WHERE ct.cards_id = ?
            '''
            cur = db.execute(card_tags_query, [card_data['id']])
            tags_data = cur.fetchall()
            card_tags = [t['tag_name'] for t in tags_data]
            card = Card(
                card_data['id'],
                card_data['type'],
                card_data['front'],
                card_data['back'],
                card_data['known'],
                card_tags)
            cards.append(card)

    tags_query = '''
            SELECT id, tag_name
            FROM tag
            ORDER BY id DESC
        '''

    cur = db.execute(tags_query)
    tags = cur.fetchall()
    return render_template('cards.html', cards=cards, tags=tags, filter_name=filter_name)


@app.route('/add', methods=['POST'])
def add_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with get_db() as db:
        insert_card_query = 'INSERT INTO cards (type, front, back) VALUES (?, ?, ?)'
        cur = db.execute(
            insert_card_query,
            [request.form['type'],
            request.form['front'],
            request.form['back']])

        tags = request.form.getlist('tag[]')
        card_id = cur.lastrowid
        insert_card_tag_query = 'INSERT INTO cards_tag VALUES (?, ?)'

        for tag_id in tags:
            db.execute(
                insert_card_tag_query,
                [card_id, tag_id])

    flash('New card was successfully added.')
    return redirect(url_for('cards'))


@app.route('/edit/<card_id>')
def edit(card_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    Tag = namedtuple('Tag', ['id', 'tag_name', 'checked'])
    with get_db() as db:
        query = '''
            SELECT id, type, front, back, known
            FROM cards
            WHERE id = ?
        '''
        cur = db.execute(query, [card_id])
        card = cur.fetchone()

        tags_query = '''
            select t.id, t.tag_name, ct.cards_id is not null as checked
            from tag t
            left join cards_tag ct on ct.tag_id = t.id
            and ct.cards_id = ?
        '''

        cur = db.execute(tags_query, [card_id])
        tags_data = cur.fetchall()
        tags = []

        for tag_data in tags_data:
            tag = Tag(
                tag_data['id'],
                tag_data['tag_name'],
                True if tag_data['checked'] else False
            )
            tags.append(tag)

    return render_template('edit.html', card=card, tags=tags)


@app.route('/edit_card', methods=['POST'])
def edit_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    selected = request.form.getlist('known')
    known = bool(selected)
    tags = request.form.getlist('tag[]')

    with get_db() as db:
        command = '''
            UPDATE cards
            SET
              type = ?,
              front = ?,
              back = ?,
              known = ?
            WHERE id = ?
        '''
        db.execute(command,
                   [request.form['type'],
                    request.form['front'],
                    request.form['back'],
                    known,
                    request.form['card_id']
                    ])


        current_tags_query = '''
            select t.id 
            from tag t
            join cards_tag ct on ct.tag_id = t.id
            where ct.cards_id = ?
        '''
        cur = db.execute(current_tags_query,
                         [request.form['card_id']])
        current_tags_data = cur.fetchall()
        cur_tags = set([t['id'] for t in current_tags_data])
        updated_tags = set([int(t) for t in tags])

        tag_ids_to_remove = list(cur_tags - updated_tags)
        tag_ids_to_add = list(updated_tags - cur_tags)

        remove_query = '''
            delete from cards_tag
            where cards_id = ? 
            and tag_id = ?
        '''
        for tag_id in tag_ids_to_remove:
            db.execute(remove_query,
                       [request.form['card_id'],
                        tag_id])
        add_query = '''
            insert into cards_tag values (?, ?)
        '''
        for tag_id in tag_ids_to_add:
            db.execute(add_query,
                       [request.form['card_id'],
                        tag_id])

    flash('Card saved.')
    return redirect(url_for('cards'))


@app.route('/edit_tag')
def edit_tag():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    tags_query = '''
                SELECT id, tag_name
                FROM tag
                ORDER BY id DESC
            '''
    with get_db() as db:
        cur = db.execute(tags_query)
        tags = cur.fetchall()
    return render_template('tags.html', tags=tags)


@app.route('/edit_tag', methods=['POST'])
def edit_tags():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.form['action'] == 'remove':
        return redirect(url_for('delete_tag', tag_id=request.form['tag[]']))

    tag_id = request.form['tag[]']
    tag_name = request.form['tag_name']

    add_query = '''
        insert into tag (tag_name) values (?)
    '''

    update_query = '''
        update tag set tag_name = ? where id = ?
    '''
    app.logger.info(tag_id)
    with get_db() as db:
        if tag_id == '0':
            db.execute(
                add_query,
                [tag_name]
            )
            flash('Tag added.')
        else:
            db.execute(
                update_query,
                [tag_name,
                 tag_id]
            )
            flash('Tag edited.')
    return redirect(url_for('edit_tag'))


@app.route('/delete_tag')
def delete_tag():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    tag_id = request.args['tag_id']

    if tag_id == '0':
        return redirect(url_for('edit_tag'))

    db = get_db()
    db.execute('DELETE FROM tag WHERE id = ?', [tag_id])
    db.commit()
    flash('Tag deleted.')

    return redirect(url_for('edit_tag'))


@app.route('/delete/<card_id>')
def delete(card_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM cards WHERE id = ?', [card_id])
    db.commit()
    flash('Card deleted.')
    return redirect(url_for('cards'))


@app.route('/general')
@app.route('/general/<card_id>')
def general(card_id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return memorize("general", card_id)


@app.route('/code')
@app.route('/code/<card_id>')
def code(card_id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return memorize("code", card_id)


def memorize(card_type, card_id):
    if card_type == "general":
        type = 1
    elif card_type == "code":
        type = 2
    else:
        return redirect(url_for('cards'))

    if card_id:
        card = get_card_by_id(card_id)
    else:
        card = get_card(type)
    if not card:
        flash("You've learned all the " + card_type + " cards.")
        return redirect(url_for('cards'))
    short_answer = (len(card['back']) < 75)
    return render_template('memorize.html',
                           card=card,
                           card_type=card_type,
                           short_answer=short_answer)


def get_card(type):
    db = get_db()

    query = '''
      SELECT
        id, type, front, back, known
      FROM cards
      WHERE
        type = ?
        and known = 0
      ORDER BY RANDOM()
      LIMIT 1
    '''

    cur = db.execute(query, [type])
    return cur.fetchone()


def get_card_by_id(card_id):
    db = get_db()

    query = '''
      SELECT
        id, type, front, back, known
      FROM cards
      WHERE
        id = ?
      LIMIT 1
    '''

    cur = db.execute(query, [card_id])
    return cur.fetchone()


@app.route('/mark_known/<card_id>/<card_type>')
def mark_known(card_id, card_type):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE cards SET known = 1 WHERE id = ?', [card_id])
    db.commit()
    flash('Card marked as known.')
    return redirect(url_for(card_type))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username or password!'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid username or password!'
        else:
            session['logged_in'] = True
            session.permanent = True  # stay logged in
            return redirect(url_for('cards'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You've logged out")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
