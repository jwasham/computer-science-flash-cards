import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)
nameDB='cards.db'
pathDB='db'

def load_config():
    app.config.update(dict(
        DATABASE=os.path.join(app.root_path, pathDB, nameDB),
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default'
    ))
    app.config.from_envvar('CARDS_SETTINGS', silent=True)

if __name__ == "__main__" or __name__ == "flash_cards":
    load_config()

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

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('list_db'))
    else:
        return redirect(url_for('login'))


@app.route('/cards')
def cards():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    query = '''
        SELECT id, type, front, back, known
        FROM cards
        ORDER BY id DESC
    '''
    cur = db.execute(query)
    cards = cur.fetchall()
    tags = getAllTag()
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
    if(query is None):
        query = "where type = {0}".format(filter_name)
        filter_name = int(filter_name)

    if not query:
        return redirect(url_for('show'))

    db = get_db()
    fullquery = "SELECT id, type, front, back, known FROM cards " + \
        query + " ORDER BY id DESC"
    cur = db.execute(fullquery)
    cards = cur.fetchall()
    tags = getAllTag()
    return render_template('show.html', cards=cards, tags=tags, filter_name=filter_name)


@app.route('/add', methods=['POST'])
def add_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('INSERT INTO cards (type, front, back) VALUES (?, ?, ?)',
               [request.form['type'],
                request.form['front'],
                request.form['back']
                ])
    db.commit()
    flash('New card was successfully added.')
    return redirect(url_for('cards'))


@app.route('/edit/<card_id>')
def edit(card_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    query = '''
        SELECT id, type, front, back, known
        FROM cards
        WHERE id = ?
    '''
    cur = db.execute(query, [card_id])
    card = cur.fetchone()
    tags = getAllTag()
    return render_template('edit.html', card=card, tags=tags)


@app.route('/edit_card', methods=['POST'])
def edit_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    selected = request.form.getlist('known')
    known = bool(selected)
    db = get_db()
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
    db.commit()
    flash('Card saved.')
    return redirect(url_for('show'))


@app.route('/delete/<card_id>')
def delete(card_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM cards WHERE id = ?', [card_id])
    db.commit()
    flash('Card deleted.')
    return redirect(url_for('cards'))

@app.route('/memorize')
@app.route('/memorize/<card_type>')
@app.route('/memorize/<card_type>/<card_id>')
def memorize(card_type, card_id=None):
    tag = getTag(card_type)
    if tag is None:
        return redirect(url_for('cards'))

    if card_id:
        card = get_card_by_id(card_id)
    else:
        card = get_card(card_type)
    if not card:
        flash("You've learned all the '" + tag[1] + "' cards.")
        return redirect(url_for('show'))
    short_answer = (len(card['back']) < 75)
    tags = getAllTag()
    card_type = int(card_type)
    return render_template('memorize.html',
                           card=card,
                           card_type=card_type,
                           short_answer=short_answer, tags=tags)

@app.route('/memorize_known')
@app.route('/memorize_known/<card_type>')
@app.route('/memorize_known/<card_type>/<card_id>')
def memorize_known(card_type, card_id=None):
    tag = getTag(card_type)
    if tag is None:
        return redirect(url_for('cards'))

    if card_id:
        card = get_card_by_id(card_id)
    else:
        card = get_card_already_known(card_type)
    if not card:
        flash("You haven't learned any '" + tag[1] + "' cards yet.")
        return redirect(url_for('show'))
    short_answer = (len(card['back']) < 75)
    tags = getAllTag()
    card_type = int(card_type)
    return render_template('memorize_known.html',
                           card=card,
                           card_type=card_type,
                           short_answer=short_answer, tags=tags)


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
    return redirect(url_for('memorize', card_type=card_type))

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
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You've logged out")
    return redirect(url_for('index'))


def getAllTag():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    query = '''
        SELECT id, tagName
        FROM tags
        ORDER BY id ASC
    '''
    cur = db.execute(query)
    tags = cur.fetchall()
    return tags


@app.route('/tags')
def tags():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    tags = getAllTag()
    return render_template('tags.html', tags=tags, filter_name="all")


@app.route('/addTag', methods=['POST'])
def add_tag():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('INSERT INTO tags (tagName) VALUES (?)',
               [request.form['tagName']])
    db.commit()
    flash('New tag was successfully added.')
    return redirect(url_for('tags'))


@app.route('/editTag/<tag_id>')
def edit_tag(tag_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    tag = getTag(tag_id)
    return render_template('editTag.html', tag=tag)


@app.route('/updateTag', methods=['POST'])
def update_tag():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    command = '''
        UPDATE tags
        SET
          tagName = ?
        WHERE id = ?
    '''
    db.execute(command,
               [request.form['tagName'],
                request.form['tag_id']
                ])
    db.commit()
    flash('Tag saved.')
    return redirect(url_for('tags'))

def init_tag():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('INSERT INTO tags (tagName) VALUES (?)',
               ["general"])
    db.commit()
    db.execute('INSERT INTO tags (tagName) VALUES (?)',
               ["code"])
    db.commit()
    db.execute('INSERT INTO tags (tagName) VALUES (?)',
               ["bookmark"])
    db.commit()

@app.route('/show')
def show():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    tags = getAllTag()
    return render_template('show.html', tags=tags, filter_name="")

def getTag(tag_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    query = '''
        SELECT id, tagName
        FROM tags
        WHERE id = ?
    '''
    cur = db.execute(query, [tag_id])
    tag = cur.fetchone()
    return tag

@app.route('/bookmark/<card_type>/<card_id>')
def bookmark(card_type, card_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE cards SET type = ? WHERE id = ?',[card_type,card_id])
    db.commit()
    flash('Card saved.')
    return redirect(url_for('memorize', card_type=card_type))

@app.route('/list_db')
def list_db():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    dbs = [f for f in os.listdir(pathDB) if os.path.isfile(os.path.join(pathDB, f))]
    dbs = list(filter(lambda k: '.db' in k, dbs))
    return render_template('listDb.html', dbs=dbs)

@app.route('/load_db/<name>')
def load_db(name):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    global nameDB
    nameDB=name
    load_config()
    handle_old_schema()
    return redirect(url_for('memorize', card_type="1"))

@app.route('/create_db')
def create_db():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('createDb.html')

@app.route('/init', methods=['POST'])
def init():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    global nameDB
    nameDB = request.form['dbName'] + '.db'
    load_config()
    init_db()
    init_tag()
    return redirect(url_for('index'))

def check_table_tag_exists():
    db = get_db()
    cur = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tags'")
    result = cur.fetchone()
    return result

def create_tag_table():
    db = get_db()
    with app.open_resource('data/handle_old_schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def handle_old_schema():
    result = check_table_tag_exists()
    if(result is None):
        create_tag_table()
        init_tag()

def get_card_already_known(type):
    db = get_db()

    query = '''
      SELECT
        id, type, front, back, known
      FROM cards
      WHERE
        type = ?
        and known = 1
      ORDER BY RANDOM()
      LIMIT 1
    '''

    cur = db.execute(query, [type])
    return cur.fetchone()

@app.route('/mark_unknown/<card_id>/<card_type>')
def mark_unknown(card_id, card_type):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE cards SET known = 0 WHERE id = ?', [card_id])
    db.commit()
    flash('Card marked as unknown.')
    return redirect(url_for('memorize_known', card_type=card_type))

if __name__ == '__main__':
    app.run(host='0.0.0.0')
