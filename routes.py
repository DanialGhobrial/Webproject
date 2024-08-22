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
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    random_data = get_random_data()
    cur.execute('SELECT * FROM Base')
    bases = cur.fetchall()
    if 'user' in session:
        return render_template('home.html', data=random_data, bases=bases, title="Home")
    else:
        return render_template('home_not_logged_in.html', data=random_data, bases=bases, title="Home")


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
    if 'user' in session:
        return render_template('menu.html', results=results, bases=bases, title="Menu")
    else:
        return render_template('menuout.html', results=results)


# Route for offers Page
@app.route('/offers')
def offers():
    return render_template("offers.html", title="Offers")


# Route for stores page
@app.route('/stores')
def stores():
    return render_template("stores.html", title="Stores")


# Route for Applying Promo
@app.route('/apply_promo', methods=["POST"])
def apply_promo():
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


# Route for Checkout Page
@app.route('/checkout')
def checkout():
    cart = session.get('cart', [])
    total = sum(item[4] for item in cart)
    discount = session.get('discount', 0)
    total_after_discount = total * (1 - discount)
    return render_template('checkout.html', cart=cart, total=total, total_after_discount=total_after_discount, discount=discount)


# Route for login page
@app.route('/login', methods=["GET", "POST"])
def login():
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
            else:
                flash("Password incorrect", "error")
        else:
            flash("Username does not exist", "error")
    # render this template regardless of get/post
    return render_template('login.html')


# Route for signup page
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
        flash("Sign Up Successful", "success")
        return redirect("/login")
    return render_template('signup.html')


# Route for logout
@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    # Redirect to the home page
    flash("Logged out successfully.", "success")
    return redirect('/')


# Route for logout
@app.route('/completeorder')
def completeorder():
    if session['cart'] == []:
        flash("Please add at least one pizza to your order.", "error")
    else:
        session['cart'] = []
        flash("Order successfully submited.", "success")
    return redirect('/')


# Route to clear cart
@app.route('/clearcart')
def clearcart():
    session['cart'] = []
    return redirect('/menu')


# Route to add something to cart from menu page
@app.post('/menucart')
def menucart():
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
        cart = session['cart']
        cart.append((pizza_id, pizza_name, base_id, item_price))
        session['cart'] = cart
    else:
        session['cart'] = [(pizza_id, pizza_name, base_id, item_price)]

    return redirect("/menu")


# Route for cart
@app.post('/cart')
def cart():
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
        cart = session['cart']
        cart.append((pizza_id, pizza_name, base_id, base_name, item_price))
        session['cart'] = cart
    else:
        session['cart'] = [(pizza_id, pizza_name, base_id, base_name, item_price)]

    return redirect("/menu")


# Route to submit order to the database
@app.post('/submit')
def submit():
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


@app.route('/your_orders')
def your_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    user_id = session['user_id']
    orders = get_orders_by_user(user_id)
    return render_template('your_orders.html', orders=orders)

# Custom error handling for page not found errors
app.errorhandler(404)
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
