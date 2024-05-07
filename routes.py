from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


@app.route('/')
def home():
    return render_template("home.html", title="Home")


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


@app.route('/offers')
def offers():
    return render_template("offers.html", title="Contact")


@app.route('/stores')
def stores():
    return render_template("stores.html", title="About")


@app.route('/menu')
def menu():
    conn = sqlite3.connect('Database/pizza.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM Pizza')
    results = cur.fetchall()
    return render_template('menu.html', results=results)


if __name__ == "__main__":
    app.run(debug=True)
