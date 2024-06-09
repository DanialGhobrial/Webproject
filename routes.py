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
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Fetch the selected pizza
    cur.execute('SELECT * FROM Pizza WHERE id=?', (id,))
    pizza = cur.fetchone()
    # Fetch all bases
    cur.execute('SELECT * FROM Base')
    bases = cur.fetchall()
    return render_template('pizza.html', pizza=pizza, bases=bases)


# Route for Pizzaout.html Page
@app.route('/pizzaout/<int:id>')
def pizzaout(id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Fetch the selected pizza
    cur.execute('SELECT * FROM Pizza WHERE id=?', (id,))
    pizza = cur.fetchone()
    # Fetch all bases
    cur.execute('SELECT * FROM Base')
    bases = cur.fetchall()
    return render_template('pizzaout.html', pizza=pizza, bases=bases)

# Route for menu page
@app.route('/menu')
def menu():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM Pizza')
    results = cur.fetchall()
    return render_template('menu.html', results=results)


@app.route('/menuout')
def menuout():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM Pizza')
    results = cur.fetchall()
    return render_template('menuout.html', results=results)


@app.route('/offers')
def offers():
    return render_template("offers.html", title="Offers")


@app.route('/stores')
def stores():
    return render_template("stores.html", title="Stores")


@app.route('/checkout')
def checkout():
    return render_template("checkout.html", title="Checkout")


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
    # render this template regardless of get/post
    return render_template('login.html')


@app.route('/signup', methods=["GET", "POST"])
def signup():
    # if the user posts from the signup page
    if request.method == "POST":
        # add the new username and hashed password to the database
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        # hash it with the cool security function
        hashed_password = generate_password_hash(password)
        # write it as a new user to the database
        sql = "INSERT INTO user (username,password,address) VALUES (?,?,?)"
        query_db(sql, (username, hashed_password, address))
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
    pizza_id = request.form['id']
    pizza_name = request.form['name']
    base_id = request.form['base_id']

    # Fetch base name using base_id
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM Base WHERE id=?', (base_id,))
    base = cur.fetchone()
    base_name = base[1]

    if "cart" in session:
        cart = session['cart']
        cart.append((pizza_id, pizza_name, base_id, base_name))
        session['cart'] = cart
    else:
        session['cart'] = [(pizza_id, pizza_name, base_id, base_name)]

    return redirect("/menu")


@app.post('/submit')
def submit():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cart = session['cart']
    userid = session['user'][0]
    for item in cart:
        pizza_id, _, base_id, _ = item
        cursor.execute('INSERT INTO Orders (userid, pizzaid, baseid) VALUES (?, ?, ?)', (userid, pizza_id, base_id))
    conn.commit()
    conn.close()
    return redirect("/clearcart")


if __name__ == "__main__":
    app.run(debug=True)
