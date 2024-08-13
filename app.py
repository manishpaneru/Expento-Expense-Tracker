import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Initialize Flask app 
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = 'manish_paneru_123'

# Database setup - Commented out as you mentioned you already have the database
#def create_database():
#    conn = sqlite3.connect('spend.db')  # Adjust the database name if needed
#    cursor = conn.cursor()
#    # ... (Add your SQL code to create tables here)
#    conn.commit()
#    conn.close()

# Call the function to create the database - Commented out
#create_database() 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username').lower()
        password = request.form.get('password')

        if not username or not password:
            return render_template('index.html', error="Please fill in all fields")

        with sqlite3.connect('spend.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM register WHERE LOWER(username) = ?', (username,)) # Case-insensitive comparison
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

            # Fetch username
            cursor.execute('SELECT username FROM register WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0]

            # Fetch expenses
            cursor.execute('SELECT * FROM expenses WHERE user_id = ?', (user_id,))
            expenses = cursor.fetchall()

            # Calculate total expenses
            total_expenses = sum(expense[5] for expense in expenses)  # Assuming 'amount' is at index 5

        return render_template('home.html', expenses=expenses, username=username, total_expenses=total_expenses)
    else:
        return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').lower() 
        password = request.form.get('password')

        # Hash the password securely
        hashed_password = generate_password_hash(password)

        # Basic validation
        if not username or not password:
            return render_template('register.html', error="Please fill in all fields")

        # Try to insert into the database
        try:
            with sqlite3.connect('spend.db') as conn:
                cursor = conn.cursor()

                # 1. Insert into 'register' table
                cursor.execute('''
                    INSERT INTO register (username, password) 
                    VALUES (?, ?)
                ''', (username, hashed_password))

                # 2. Get the newly created user's ID
                user_id = cursor.lastrowid

                # 3. Insert into 'users' table
                date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current date and time
                cursor.execute('''
                    INSERT INTO users (id, name, date_created) 
                    VALUES (?, ?, ?)
                ''', (user_id, username, date_created))

                conn.commit()

        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists")

        # Redirect to index upon successful registration
        return redirect(url_for('index'))

    # If it's a GET request, just display the registration form
    return render_template('register.html')


@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:
        user_id = session['user_id']
        
        with sqlite3.connect('spend.db') as conn:
            cursor = conn.cursor()

            # Fetch username
            cursor.execute('SELECT username FROM register WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0]
            else:
                return render_template('home.html', error="User not found") 

            # Get expense data from the form (excluding date and time)
            topic = request.form.get('expense_topic')
            amount = float(request.form.get('amount'))

            # Get current date and time
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            time = now.strftime('%H:%M:%S')

            # Basic validation (excluding date and time)
            if not topic or amount is None:
                # Fetch existing expenses and display an error
                cursor.execute('SELECT * FROM expenses WHERE user_id = ?', (user_id,))
                expenses = cursor.fetchall()
                return render_template('home.html', error="Please fill in all fields", expenses=expenses, username=username)

            try:
                # Insert into 'expenses' table
                cursor.execute('''
                    INSERT INTO expenses (username, date, time, topic, amount, user_id) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, date, time, topic, amount, user_id))
                conn.commit()
            except sqlite3.Error as e:
                return render_template('home.html', error=f"Database error: {e}")

        # Fetch updated expenses and re-render home page
        return redirect(url_for('home'))

    else:
        return redirect(url_for('index'))
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user_id from the session
    return redirect(url_for('index'))  # Redirect to the index page

if __name__ == '__main__':
    app.run(debug=True)










