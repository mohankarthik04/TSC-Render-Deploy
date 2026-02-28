from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import psycopg2.extras
import re
import os

app = Flask(__name__)
app.secret_key = 'mks47'


# ==========================================
# DATABASE CONNECTION (Render Ready)
# ==========================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://tsc_user:Y3T7jzCwDS9YPWUC3SkD6JltawgQgepn@dpg-d6gtldlm5p6s73a967fg-a.oregon-postgres.render.com/tsc"
)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


# ==========================================
# AUTO CREATE TABLES
# ==========================================

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # ACCOUNTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            username VARCHAR(100) UNIQUE,
            email VARCHAR(150) UNIQUE,
            password VARCHAR(200)
        );
    """)

    # POSTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100),
            title VARCHAR(200),
            content TEXT,
            date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE
        );
    """)

    # ANSWERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100),
            content TEXT,
            query_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # CONTACT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100),
            email VARCHAR(150),
            issue TEXT,
            account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()


# Run table creation at startup
create_tables()


# ==========================================
# HOME
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')


# ==========================================
# REGISTER
# ==========================================

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
            'SELECT * FROM accounts WHERE username=%s OR email=%s',
            (username, email)
        )
        account = cursor.fetchone()

        if account:
            flash('⚠️ Account Already Exists!', 'warning')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('⚠️ Invalid Email!', 'danger')
        else:
            cursor.execute(
                'INSERT INTO accounts (first_name,last_name,username,email,password) VALUES (%s,%s,%s,%s,%s)',
                (fname, lname, username, email, password)
            )
            conn.commit()
            flash('✔ Registration Successful! Please login.', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        cursor.close()
        conn.close()

    return render_template('register.html')


# ==========================================
# LOGIN
# ==========================================

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(
            'SELECT * FROM accounts WHERE email=%s AND password=%s',
            (email, password)
        )
        account = cursor.fetchone()

        cursor.close()
        conn.close()

        if account:
            session['user_id'] = account['id']
            session['username'] = account['username']
            session['first_name'] = account['first_name']
            return redirect(url_for('user01'))
        else:
            flash('⚠️ Invalid Credentials!', 'danger')

    return render_template('login.html')


# ==========================================
# DASHBOARD
# ==========================================

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

    return render_template('user01.html', user=user)


# ==========================================
# POST QUERY
# ==========================================

@app.route('/postquery/', methods=['GET', 'POST'])
def postquery():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO posts (username,title,content,account_id)
            VALUES (%s,%s,%s,%s)
        """, (session['username'], title, content, session['user_id']))

        conn.commit()
        cursor.close()
        conn.close()

        flash('✔ Query Posted!', 'success')
        return redirect(url_for('postquery'))

    return render_template('postquery.html')


# ==========================================
# ALL QUERIES
# ==========================================

@app.route('/allqueries/')
def allqueries():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT * FROM posts ORDER BY date_posted DESC")
    posts = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('allqueries.html', posts=posts)


# ==========================================
# LOGOUT
# ==========================================

@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ==========================================
# STATIC PAGES
# ==========================================

@app.route('/queriesraised/')
def contact():
    return render_template('queriesraised.html')

@app.route('/contact/')
def contact():
    return render_template('contact.html')

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


if __name__ == '__main__':
    app.run(debug=True)