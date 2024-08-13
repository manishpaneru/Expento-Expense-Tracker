import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = 'manish_paneru_123'

@app.route('/', methods=['GET, 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username').lower()
        password = request.form.get('password')

        if not username or not password:
            return render_template('index.html', error="Please fill in all fields")

        with sqlite3.connect('spend.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM register WHERE LOWER(username) = ?', (username,))
            user = cursor.fetchone()

            if user:
                if check_password_hash(user[2], password):
                    session['user_id'] = user[0]
                    return redirect(url_for('home'))
                else:
                    return render_template('index.html', error="Wrong password, bro")
            else:
                return render_template('index.html', error="Username doesn't exist, bro")

    return render_template('index.html')

@app.route('/home')
def home():
    if 'user_id' in session:
        user_id = session['user_id']
        with sqlite3.connect('spend.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM register WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0]

            cursor.execute('SELECT * FROM expenses WHERE user_id = ?', (user_id,))
            expenses = cursor.fetchall()
            total_expenses = sum(expense[5] for expense in expenses)

        return render_template('home.html', expenses=expenses, username=username, total_expenses=total_expenses)
    else:
        return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').lower()
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        if not username or not password:
            return render_template('register.html', error="Please fill in all fields")

        try:
            with sqlite3.connect('spend.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO register (username, password)
                    VALUES (?, ?)
                ''', (username, hashed_password))

                user_id = cursor.lastrowid
                date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO users (id, name, date_created)
                    VALUES (?, ?, ?)
                ''', (user_id, username, date_created))

                conn.commit()

        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists")

        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:
        user_id = session['user_id']

        with sqlite3.connect('spend.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM register WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0]
            else:
                return render_template('home.html', error="User not found")

            topic = request.form.get('expense_topic')
            amount = float(request.form.get('amount'))
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            time = now.strftime('%H:%M:%S')

            if not topic or amount is None:
                cursor.execute('SELECT * FROM expenses WHERE user_id = ?', (user_id,))
                expenses = cursor.fetchall()
                return render_template('home.html', error="Please fill in all fields", expenses=expenses, username=username)

            try:
                cursor.execute('''
                    INSERT INTO expenses (username, date, time, topic, amount, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, date, time, topic, amount, user_id))
                conn.commit()
            except sqlite3.Error as e:
                return render_template('home.html', error=f"Database error: {e}")

        return redirect(url_for('home'))
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
