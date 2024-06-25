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
    random_data = get_random_data()
    return render_template('home.html', data=random_data)


# Function to get random data from the 'Movie' table
def get_random_data():
    with sqlite3.connect("Database/pizza.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Pizza ORDER BY RANDOM() LIMIT 4")
        data = cursor.fetchall()
    return data


# Route for pizza Page
@app.route('/pizza/<int:id>')
def pizza(id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    try:
        # Fetch the selected pizza details
        cur.execute('SELECT * FROM Pizza WHERE id=?', (id,))
        pizza = cur.fetchone()
        if not pizza:
            raise ValueError(f"No pizza found with ID {id}")
        # Fetch ingredients of the selected pizza
        cur.execute('''
            SELECT Ingredients.Name
            FROM Ingredients
            JOIN PizzaIngredients ON Ingredients.ID = PizzaIngredients.IngredientID
            WHERE PizzaIngredients.PizzaID = ?
        ''', (id,))
        ingredients = [row[0] for row in cur.fetchall()]
        # Fetch all bases (assuming this is unchanged)
        cur.execute('SELECT * FROM Base')
        bases = cur.fetchall()
        conn.close()
        return render_template('pizza.html', pizza=pizza, bases=bases, ingredients=ingredients)
    except Exception as e:
        print(f"Error fetching pizza details: {e}")
        conn.close()
        return render_template('error.html', message="An error occurred while fetching pizza details.")


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
    cur.execute('SELECT * FROM Base')
    bases = cur.fetchall()
    conn.close()
    return render_template('menu.html', results=results, bases=bases)


# Route for menu page when loged out 
@app.route('/menuout')
def menuout():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM Pizza')
    results = cur.fetchall()
    return render_template('menuout.html', results=results)


# Route for offers Page
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


@app.post('/menucart')
def menucart():
    pizza_id = request.form['id']
    pizza_name = request.form['name']
    base_id = 1

    if "cart" in session:
        cart = session['cart']
        cart.append((pizza_id, pizza_name, base_id))
        session['cart'] = cart
    else:
        session['cart'] = [(pizza_id, pizza_name, base_id)]

    return redirect("/menu")


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


# Custom error handling for page not found errors
@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', error='Page not found'), 404


# Custom error handling for 500 (Internal Server Error) error
@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', error='Internal server error'), 500


# Custom error handling for other unexpected errors
@app.errorhandler(Exception)
def unexpected_error(error):
    return render_template('error.html', error='Something went wrong'), 500


if __name__ == "__main__":
    app.run(debug=True)
