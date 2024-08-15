''' This is the routes page for my pizza website. '''
import sqlite3
from flask import Flask, render_template, session, flash, redirect, request
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


@app.route('/')
def home():
    ''' # route for home page'''
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    random_data = get_random_data()
    cur.execute('SELECT * FROM Base')
    bases = cur.fetchall()
    if 'user' in session:
        # checks if user is in session to determine what homepage they see
        return render_template('home.html', data=random_data, bases=bases, title="Home")
    return render_template('home_not_logged_in.html', data=random_data, bases=bases, title="Home")


def get_random_data():
    ''' # Function to get random data from the Movies table '''
    with sqlite3.connect("Database/pizza.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Pizza ORDER BY RANDOM() LIMIT 4")
        data = cursor.fetchall()
    return data


@app.route('/pizza/<int:pizza_id>')
def pizza_page(pizza_id):
    ''' # route for pizza page'''
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Fetch the selected pizza details
    cur.execute('SELECT * FROM Pizza WHERE id=?', (pizza_id,))
    selected_pizza = cur.fetchone()  # Renamed variable to avoid conflict
    if not selected_pizza:
        raise ValueError(f"No pizza found with ID {pizza_id}")
    # Fetch ingredients of the selected pizza
    cur.execute('''
            SELECT Ingredients.Name
            FROM Ingredients
            JOIN PizzaIngredients ON Ingredients.ID = PizzaIngredients.IngredientID
            WHERE PizzaIngredients.PizzaID = ?
        ''', (pizza_id,))
    ingredients = [row[0] for row in cur.fetchall()]
    # Fetch all bases (assuming this is unchanged)
    cur.execute('SELECT * FROM Base')
    bases = cur.fetchall()
    conn.close()
    if 'user' in session:
        return render_template('pizza.html', pizza=selected_pizza, bases=bases, ingredients=ingredients)
    return render_template('pizzaout.html', pizza=selected_pizza, bases=bases, ingredients=ingredients)


@app.route('/menu')
def menu():
    ''' # Route for menu Page'''
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM Pizza')
    results = cur.fetchall()
    cur.execute('SELECT * FROM Base')
    bases = cur.fetchall()
    conn.close()
    if 'user' in session:
        return render_template('menu.html', results=results, bases=bases, title="Menu")
    else:
        return render_template('menuout.html', results=results)


@app.route('/offers')
def offers():
    ''' # Route for offers Page'''
    return render_template("offers.html", title="Offers")


@app.route('/stores')
def stores():
    ''' # Route for stores page'''
    return render_template("stores.html", title="Stores")


@app.route('/apply_promo', methods=["POST"])
def apply_promo():
    ''' # Route for applying Promo Codes'''
    promo_code = request.form['promo_code']
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Check if the promo code is valid
    cur.execute('SELECT id, discount FROM PromoCodes WHERE code=?', (promo_code,))
    promo = cur.fetchone()
    if promo:
        # Valid promo code
        session['promo_code_id'] = promo[0]
        session['discount'] = promo[1]
        flash(f"Promo code applied! You get {promo[1]*100}% off.", "success")
    else:
        # Invalid promo code
        flash("Invalid promo code.", "error")
    conn.close()
    return redirect('/checkout')


@app.route('/checkout')
def checkout():
    ''' # Route for the checkout page'''
    current_cart = session.get('cart', [])  # Renamed to avoid conflict
    total = sum(item[4] for item in current_cart)
    discount = session.get('discount', 0)
    total_after_discount = total * (1 - discount)
    return render_template('checkout.html', cart=current_cart, total=total, total_after_discount=total_after_discount, discount=discount)



@app.route('/login', methods=["GET", "POST"])
def login():
    '''Route for login Page'''
    # if the user posts a username and password
    if request.method == "POST":
        # get the username and password
        username = request.form['username']
        password = request.form['password']
        # try to find this user in the database
        sql = "SELECT * FROM user WHERE username = ?"
        user = query_db(sql=sql, args=(username,), one=True)
        if user:
            # we got a user!!
            # check password matches-
            if check_password_hash(user[2], password):
                # we are logged in successfully
                # Store the username in the session
                session['user'] = user
                flash("Logged in successfully", "success")
                session['cart'] = []
                return redirect("/menu")
            flash("Password incorrect", "error")
        else:
            flash("Username does not exist", "error")
    # render this template regardless of get/post
    return render_template('login.html')


@app.route('/signup', methods=["GET", "POST"])
def signup():
    ''' # Route for signup page'''
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
        flash("Sign Up Successful", "success")
        return redirect("/login")
    return render_template('signup.html')


@app.route('/logout')
def logout():
    '''Route for logout page'''
    session.clear()
    # Redirect to the home page
    flash("Logged out successfully.", "success")
    return redirect('/')


@app.route('/completeorder')
def completeorder():
    ''' # Route for completing an order'''
    # Clear all session data
    session['cart'] = []
    # Redirect to the home page
    flash("Order successfully  submited.", "success")
    return redirect('/')


@app.route('/clearcart')
def clearcart():
    ''' # Route to clear cart '''
    session['cart'] = []
    return redirect('/menu')


@app.post('/menucart')
def menucart():
    ''' # Route to add something to cart from menu page '''
    pizza_id = request.form['id']
    pizza_name = request.form['name']
    base_id = 1  # Default base ID

    # Fetch the price of the selected pizza and base
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT price FROM Pizza WHERE id=?', (pizza_id,))
    pizza_price = float(cur.fetchone()[0])  # Convert to float
    cur.execute('SELECT price FROM Base WHERE id=?', (base_id,))
    base_price = float(cur.fetchone()[0])  # Convert to float
    conn.close()

    item_price = pizza_price + base_price

    if "cart" in session:
        current_cart = session['cart']  # Renamed to avoid conflict
        current_cart.append((pizza_id, pizza_name, base_id, item_price))
        session['cart'] = current_cart
    else:
        session['cart'] = [(pizza_id, pizza_name, base_id, item_price)]

    return redirect("/menu")


@app.post('/cart')
def add_to_cart():
    ''' # Route for cart '''
    pizza_id = request.form['id']
    pizza_name = request.form['name']
    base_id = request.form['base_id']

    # Fetch base name and price using base_id
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT name, price FROM Base WHERE id=?', (base_id,))
    base = cur.fetchone()
    base_name, base_price = base[0], float(base[1])  # Convert to float

    # Fetch pizza price
    cur.execute('SELECT price FROM Pizza WHERE id=?', (pizza_id,))
    pizza_price = float(cur.fetchone()[0])  # Convert to float
    conn.close()

    item_price = pizza_price + base_price

    if "cart" in session:
        current_cart = session['cart']  # Renamed to avoid conflict
        current_cart.append((pizza_id, pizza_name, base_id, base_name, item_price))
        session['cart'] = current_cart
    else:
        session['cart'] = [(pizza_id, pizza_name, base_id, base_name, item_price)]

    return redirect("/menu")


@app.post('/submit')
def submit():
    ''' # Route to submit order to the database'''
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cart = session['cart']
    userid = session['user'][0]
    for item in cart:
        pizza_id, _, base_id, _, _ = item
        cursor.execute('INSERT INTO Orders (userid, pizzaid, baseid) VALUES (?, ?, ?)', (userid, pizza_id, base_id))
    conn.commit()
    conn.close()
    return redirect("/completeorder")


@app.errorhandler(404)
def page_not_found(error):
    ''' # Custom error handling for page not found errors'''
    return render_template('error.html', error=str(error)), 404


@app.errorhandler(500)
def internal_server_error(error):
    ''' # Custom error handling for internal server errors'''
    return render_template('error.html', error=str(error)), 500


@app.errorhandler(Exception)
def unexpected_error(error):
    ''' # Custom error handling for other unexpected errors'''
    return render_template('error.html', error=str(error)), 500


if __name__ == "__main__":
    app.run(debug=True)
