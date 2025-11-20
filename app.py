import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

db.execute("""CREATE TABLE IF NOT EXISTS transactions (
           id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
           user_id INTEGER NOT NULL,
           symbol TEXT NOT NULL,
           shares INTEGER NOT NULL,
           price NUMERIC NOT NULL,
           transacted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
           FOREIGN KEY (user_id) REFERENCES users(id))""")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # create list for inform from bd (symbol, shares, price, total)
    actions = []

    # select all actions from bd
    rows = db.execute(
        "SELECT symbol, SUM(shares) FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", session["user_id"])
    temp_total = 0
    for row in rows:
        symbol = row["symbol"]
        shares = row["SUM(shares)"]

        price = lookup(symbol)["price"]
        total = float(price) * float(shares)
        temp_total += total

        # update list
        actions.append({"symbol": symbol, "shares": shares,
                       "price": usd(price), "total": usd(total)})

    row_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = row_cash[0]["cash"]
    full_total = cash + temp_total
    return render_template("index.html", actions=actions, cash=usd(cash), total=usd(full_total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        symbol = request.form.get("symbol")
        if not symbol:
            return apology("missing symbol", 400)
        search = lookup(symbol)
        if not search:
            return apology("invalid symbol", 400)
        temp_shares = request.form.get("shares")
        if not temp_shares:
            return apology("missing shares", 400)
        try:
            shares = int(temp_shares)
            if shares <= 0:
                return apology("invalid shares", 400)
        except ValueError:
            return apology("invalid shares", 400)
        if shares != int(temp_shares):
            return apology("invalid shares", 400)

        rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        balance = rows[0]["cash"]
        if int(balance) < shares * int(search["price"]):
            return apology("can't afford", 400)

        # update purchase in table "transactions"
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES(?, ?, ?, ?)",
                   session["user_id"], search["symbol"], shares, search["price"])

        # update cash in table "user"
        balance = balance - (shares * int(search["price"]))
        db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, session["user_id"])

        flash("Bought!")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    actions = []
    rows = db.execute(
        "SELECT symbol, shares, price, transacted FROM transactions WHERE user_id = ?", session["user_id"])
    for row in rows:
        symbol = row["symbol"]
        shares = row["shares"]
        price = row["price"]
        transacted = row["transacted"]

        # update list
        actions.append({"symbol": symbol, "shares": shares,
                       "price": usd(price), "transacted": transacted})
    return render_template("history.html", actions=actions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        user_symbol = request.form.get("symbol")
        if not user_symbol:
            return apology("missing symbol", 400)
        search = lookup(user_symbol)
        if not search:
            return apology("invalid symbol", 400)
        price = usd(search["price"])
        name = search["name"]
        symbol = search["symbol"]
        return render_template("quoted.html", price=price, name=name, symbol=symbol)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username and password was submitted
        if not username:
            return apology("must provide username", 400)
        elif not password:
            return apology("must provide password", 400)
        elif not confirmation:
            return apology("must provide confim_password", 400)
        elif confirmation != password:
            return apology("passwords do not match", 400)

        hash_pasword = generate_password_hash(password)
        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash_pasword)
        except ValueError:
            return apology("This username already exist", 400)

        flash("Registered!")
        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        users_symbol = request.form.get("symbol")
        if not users_symbol:
            return apology("missing symbol")
        users_shares = request.form.get("shares")
        if not users_shares:
            return apology("missing shares")
        if not int(users_shares) > 0:
            return apology("shares must be positive")

        row_all_shares = db.execute(
            "SELECT SUM(shares) FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol", session["user_id"], users_symbol)
        all_shares = row_all_shares[0]["SUM(shares)"]
        if int(users_shares) > all_shares:
            return apology("to many shares")

        current_price = lookup(users_symbol)["price"]
        total = int(users_shares) * current_price

        # update cash in table "user"
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total, session["user_id"])

        # update purchase in table "transactions"
        users_shares = int(users_shares) * (-1)
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES(?, ?, ?, ?)",
                   session["user_id"], users_symbol, users_shares, current_price)

        flash("Sold!")
        return redirect("/")
    else:
        symbol = []
        rows = db.execute(
            "SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", session["user_id"])
        for row in rows:
            symbol.append(row["symbol"])
        return render_template("sell.html", symbols=symbol)


@app.route("/cash", methods=["GET", "POST"])
@login_required
def add_cash():
    if request.method == "POST":
        amount = request.form.get("cash")
        if not amount:
            return apology("missing amount")
        if int(amount) < 0:
            return apology("must be a positive number")
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", amount, session["user_id"])
        flash("Added!")
        return redirect("/")
    else:
        return render_template("cash.html")

if __name__ == "__main__":
    app.run(debug=True)