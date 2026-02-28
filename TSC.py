from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import psycopg2.extras
import re

app = Flask(__name__)
app.secret_key = 'mks47'


# ==============================
# DATABASE CONNECTION (PostgreSQL)
# ==============================

def get_db_connection():
    return psycopg2.connect(
        os.eniron.get("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )


# ==============================
# HOME PAGE
# ==============================

@app.route('/')
def index():
    return render_template('index.html')


# ==============================
# REGISTER
# ==============================

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(
            'SELECT * FROM accounts WHERE username = %s OR email = %s',
            (username, email)
        )
        account = cursor.fetchone()

        if account:
            flash('⚠️ Account Already Exists ! Try Logging In.', 'warning')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('⚠️ Invalid Email Address !', 'danger')
        elif not re.match(r'[A-Za-z0-9]+$', username):
            flash('⚠️ Username Must Contain only Characters and Numbers !', 'warning')
        else:
            cursor.execute(
                'INSERT INTO accounts (first_name, last_name, username, email, password) VALUES (%s, %s, %s, %s, %s)',
                (fname, lname, username, email, password)
            )
            conn.commit()
            flash(f'✔ Successfully Registered {fname} {lname} ! Please Login.', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        cursor.close()
        conn.close()

    return render_template('register.html')


# ==============================
# LOGIN
# ==============================

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(
            'SELECT * FROM accounts WHERE email = %s AND password = %s',
            (email, password)
        )
        account = cursor.fetchone()

        cursor.close()
        conn.close()

        if account:
            session['user_id'] = account['id']
            session['first_name'] = account['first_name']
            session['last_name'] = account['last_name']
            session['username'] = account['username']
            session['email'] = account['email']
            session['password'] = account['password']
            return redirect(url_for('user01'))
        else:
            flash("⚠️ Credentials Doesn't Align !", 'warning')

    return render_template('login.html')


# ==============================
# USER DASHBOARD
# ==============================

@app.route('/user01/')
def user01():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        "SELECT first_name, last_name, email FROM accounts WHERE id = %s",
        (session['user_id'],)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    flash(f"~ Welcome Home, {user['first_name']} {user['last_name']} ! ~", 'success')

    return render_template('user01.html', posts=user)


# ==============================
# POST QUERY
# ==============================

@app.route('/postquery/', methods=['GET', 'POST'])
def postquery():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        title = request.form['title']
        content = request.form['content']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO posts (username, title, content, date_posted, account_id)
            VALUES (%s, %s, %s, NOW(), %s)
        """, (username, title, content, session['user_id']))

        conn.commit()
        cursor.close()
        conn.close()

        flash('✔ Query Raised Successfully !', 'success')
        return redirect(url_for('postquery'))

    return render_template('postquery.html')


# ==============================
# ALL QUERIES
# ==============================

@app.route('/allqueries/')
def allqueries():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("""
        SELECT id, title, content, date_posted, username
        FROM posts
        ORDER BY date_posted DESC
    """)

    posts = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('allqueries.html', posts=posts)


# ==============================
# QUERY DETAIL
# ==============================

@app.route('/query_detail/<int:post_id>/')
def query_detail(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM answers
        WHERE query_id = %s
        ORDER BY created_at DESC
    """, (post_id,))
    answers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('query_detail.html', post=post, answers=answers)


# ==============================
# SUBMIT ANSWER
# ==============================

@app.route('/query/<int:post_id>/submit_answer/', methods=['GET', 'POST'])
def submit_answer(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST':
        username = request.form['username']
        content = request.form['content']

        cursor.execute("""
            INSERT INTO answers (username, content, query_id)
            VALUES (%s, %s, %s)
        """, (username, content, post_id))

        conn.commit()
        flash('✔ Response Posted Successfully!', 'success')

    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('submit_answer.html', post=post)


# ==============================
# STATIC PAGES
# ==============================

@app.route('/faqs/')
def faqs():
    return render_template('faqs.html')


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/help/')
def help():
    return render_template('help.html')


@app.route('/updates/')
def updates():
    return render_template('updates.html')


@app.route('/notifications/')
def notifications():
    return render_template('notify.html')


# ==============================
# ACCOUNT
# ==============================

@app.route('/account/')
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = {
        'first_name': session['first_name'],
        'last_name': session['last_name'],
        'username': session['username'],
        'email': session['email'],
        'password': session['password']
    }

    return render_template('account.html', user=user)


# ==============================
# UPDATE ACCOUNT
# ==============================

@app.route('/updateaccount/', methods=['GET', 'POST'])
def updateaccount():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT * FROM accounts WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()

    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor.execute("""
            UPDATE accounts
            SET first_name=%s, last_name=%s, username=%s, email=%s, password=%s
            WHERE id=%s
        """, (fname, lname, username, email, password, session['user_id']))

        conn.commit()

        session['first_name'] = fname
        session['last_name'] = lname
        session['username'] = username
        session['email'] = email
        session['password'] = password

        flash('✔ Update Successful !', 'success')

    cursor.close()
    conn.close()

    return render_template('updateaccount.html', user=user)


# ==============================
# CONTACT
# ==============================

@app.route('/contact/', methods=['GET', 'POST'])
def contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        fname = request.form['fname']
        email = request.form['email']
        issue = request.form['issue']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contact (first_name, email, issue, account_id)
            VALUES (%s, %s, %s, %s)
        """, (fname, email, issue, session['user_id']))

        conn.commit()
        cursor.close()
        conn.close()

        flash('✔ Support Ticket Submitted !', 'success')

    return render_template('contact.html')


# ==============================
# LOGOUT
# ==============================

@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ==============================
# RUN
# ==============================

if __name__ == '__main__':
    app.run(debug=True)