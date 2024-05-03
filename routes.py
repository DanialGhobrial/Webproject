from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


# Route for the home page
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/menu', methods=['GET'])
def movie():
    conn = sqlite3.connect('Database/pizza.db')
    cur = conn.cursor()
    pizza = cur.fetchone()
    cur.execute('SELECT * FROM Pizza WHERE id=?' ("?"))
    return render_template('menu.html', pizza=pizza)


if __name__ == "__main__":
    app.run(debug=True)
