from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import psycopg2.extras
import os
import re

app = Flask(__name__)
app.secret_key = 'mks47'


# ==============================
# DATABASE CONNECTION (POSTGRESQL - RENDER)
# ==============================

def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    return conn


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
                'INSERT INTO accounts (First_Name, Last_Name, Username, Email, Password) VALUES (%s, %s, %s, %s, %s)',
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
# LOGOUT
# ==============================

@app.route('/faqs/')
def faqs():
    return render_template('faqs.html')


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