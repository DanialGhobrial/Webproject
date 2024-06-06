from flask import Flask, render_template, session, flash, redirect, request
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "Database/pizza.db"
app = Flask(__name__)
app.config['SECRET_KEY'] = "key123"


def query_db(sql, args=(), one=False):
    '''connect and query- will retun one item if one=true and can accept arguments as tuple'''
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute(sql, args)
    results = cursor.fetchall()
    db.commit()
    db.close()
    return (results[0] if results else None) if one else results


# Route for Home Page
@app.route('/')
def home():
    return render_template("home.html", title="Home")


# Route for Pizza.html Page
@app.route('/pizza/<int:id>')
def pizza(id):
    conn = sqlite3.connect('Database/pizza.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM Pizza WHERE id=?', (id,))
    pizza = cur.fetchone()
    cur.execute('SELECT * FROM Base WHERE id=?', (pizza[2],))
    base = cur.fetchone()
    cur.execute('SELECT * FROM Pizza WHERE id=?', (pizza[1],))
    topping = cur.fetchone()
    return render_template('pizza.html', pizza=pizza, base=base, topping=topping)


# Route for Checkout page
@app.route('/checkout')
def checkout():
    return render_template("checkout.html", title="checkout")


# Route for offers page
@app.route('/offers')
def offers():
    return render_template("offers.html", title="Contact")


# Route For Stores Page
@app.route('/stores')
def stores():
    return render_template("stores.html", title="About")


# Route for menu page
@app.route('/menu')
def menu():
    conn = sqlite3.connect('Database/pizza.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM Pizza')
    results = cur.fetchall()
    return render_template('menu.html', results=results)


@app.route('/login', methods=["GET", "POST"])
def login():
    # if the user posts a username and password
    if request.method == "POST":
        # get the username and password
        username = request.form['username']
        password = request.form['password']
        # try to find this user in the database- note- just keepin' it simple so usernames must be unique
        sql = "SELECT * FROM user WHERE username = ?"
        user = query_db(sql=sql, args=(username,), one=True)
        if user:
            # we got a user!!
            # check password matches-
            if check_password_hash(user[2], password):
                # we are logged in successfully
                # Store the username in the session
                session['user'] = user
                flash("Logged in successfully")
                session['cart'] = []
                return redirect("/menu")
            else:
                flash("Password incorrect")
        else:
            flash("Username does not exist")
    # render this template regardles of get/post
    return render_template('login.html')


@app.route('/signup', methods=["GET", "POST"])
def signup():
    # if the user posts from the signup page
    if request.method == "POST":
        # add the new username and hashed password to the database
        username = request.form['username']
        password = request.form['password']
        adress = request.form['adress']
        # hash it with the cool secutiry function
        hashed_password = generate_password_hash(password)
        # write it as a new user to the database
        sql = "INSERT INTO user (username,password,adress) VALUES (?,?,?)"
        query_db(sql, (username, hashed_password, adress))
        # message flashes exist in the base.html template and give user feedback
        flash("Sign Up Successful")
        return redirect("/login")
    return render_template('signup.html')


@app.route('/logout')
def logout():
    # just clear the username from the session and redirect back to the home page
    session['user'] = None
    session['cart'] = None
    return redirect('/')

@app.route('/clearcart')
def clearcart():
    session['cart'] = []
    return redirect('/menu')


@app.post('/cart')
def cart():
    id = request.form['id']
    name = request.form['name']
    if "cart" in session:
        values = session['cart']
        values.append((id, name))
        session['cart'] = values
        print(session['cart'])
    else:
        print("No cart in session")
    return redirect("/menu")


@app.post('/submit')
def submit():
    conn = sqlite3.connect('Database/pizza.db')
    cart = session['cart'][0]
    userid = session['user'][0]
    cursor = conn.cursor() 
    cursor.execute('INSERT INTO Orders (cart, userid) VALUES (?, ?)', (cart, userid))
    conn.commit() 
    return redirect("/clearcart")


if __name__ == "__main__":
    app.run(debug=True)
