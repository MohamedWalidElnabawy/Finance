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


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]

    # Pagination setup
    page = int(request.args.get("page", 1))  # current page, default = 1
    per_page = 10  # number of transactions per page
    offset = (page - 1) * per_page

    # Get total count of transactions (for pagination)
    total_transactions = db.execute(
        "SELECT COUNT(*) AS count FROM transactions WHERE user_id = ?", user_id
    )[0]["count"]
    total_pages = (total_transactions + per_page - 1) // per_page  # ceiling division

    # Get paginated transactions (latest first)
    transactions = db.execute(
        """
        SELECT symbol, shares, price, type, timestamp
        FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?;
        """,
        user_id,
        per_page,
        offset,
    )

    # Compute total value for each transaction (price * shares)
    for t in transactions:
        t["total"] = t["shares"] * t["price"]

    return render_template(
        "history.html",
        transactions=transactions,
        page=page,
        total_pages=total_pages,
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        user_id = session["user_id"]
        type = "buy"
        if not symbol:
            return apology("symbol field required", 400)
        stock = lookup(symbol)
        if not stock:
            return apology("stock not found", 400)
        if not shares:
            return apology("shares field required", 400)
        elif not shares.isdigit():
            return apology("shares must be a positive integer", 400)
        shares = int(shares)
        if shares <= 0:
            return apology("shares must be a positive integer", 400)
        total_Cost = int(shares) * stock["price"]
        user_cash = db.execute("select cash from users where id = ?", user_id)[0]
        if total_Cost > int(user_cash["cash"]):
            return apology("not enough cash")

        db.execute(
            "insert into transactions (user_id, symbol, shares, price, type,total) values (?,?,?,?,?,?)",
            user_id,
            symbol,
            shares,
            stock["price"],
            type,
            total_Cost,
        )
        new_cash = user_cash["cash"] - total_Cost
        db.execute("update users set cash = ? where id = ?", new_cash, user_id)
        flash("Bought!")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]

    # Get user's current holdings (net shares)
    stocks = db.execute(
        """
    SELECT symbol,
               SUM(
                   CASE
                       WHEN type = 'buy' THEN shares
                       WHEN type = 'sell' THEN -shares
                   END
               ) AS shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        HAVING shares > 0;
""",
        user_id,
    )

    # Get user's current cash
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    # Compute total value of portfolio
    total_value = 0
    updated_stocks = []

    for stock in stocks:
        symbol = stock["symbol"]
        shares = stock["shares"]
        quote = lookup(symbol)  # get current price
        price = quote["price"]
        total = shares * price
        total_value += total
        updated_stocks.append(
            {"symbol": symbol, "shares": shares, "price": price, "total": total}
        )

    # Grand total = cash + total stock value
    grand_total = cash + total_value

    return render_template(
        "index.html", stocks=updated_stocks, cash=cash, total=grand_total
    )


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
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("symbol field is required", 400)
        stock = lookup(symbol)
        if not stock:
            return apology("stock not found", 400)
        else:
            return render_template("quoted.html", stock=stock)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip()
        username = username.lower()
        password = request.form.get("password")
        confirmpassword = request.form.get("confirmation")
        rows = db.execute("select * from users where username = ?", username)

        if not username:
            return apology("Username field is required", 400)
        elif len(rows) != 0:
            return apology("username is already used", 400)
        elif not password:
            return apology("password field is required", 400)
        elif not confirmpassword:
            return apology("confirm password field is required", 400)
        elif not password == confirmpassword:
            return apology("passwords doesn't match")
        else:
            hash = generate_password_hash(password)
            user_id = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", username, hash
            )
            session["user_id"] = user_id
            flash("Registered successfully!")
            return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    user_id = session["user_id"]

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Validate inputs
        if not symbol:
            return apology("symbol field is required", 400)
        if not shares or not shares.isdigit():
            return apology("shares must be a positive integer", 400)

        shares = int(shares)
        if shares <= 0:
            return apology("shares must be greater than 0", 400)

        # Get user's owned shares
        result = db.execute(
            """
            SELECT SUM(
                CASE 
                    WHEN type = 'buy' THEN shares
                    WHEN type = 'sell' THEN -shares
                END
            ) AS shares
            FROM transactions
            WHERE user_id = ? AND symbol = ?
            GROUP BY symbol;
            """,
            user_id,
            symbol,
        )

        if not result or result[0]["shares"] is None or result[0]["shares"] < shares:
            return apology("not enough shares", 400)

        # Lookup current price
        stock = lookup(symbol)
        price = stock["price"]
        total_price = price * shares  # this is the money earned

        # Record sale (shares negative)
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price, type, total) VALUES (?, ?, ?, ?, ?, ?)",
            user_id,
            symbol,
            shares,  # negative shares for sell
            price,
            "sell",
            total_price,
        )

        # Update user's cash (add the money)
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?", total_price, user_id
        )

        return redirect("/")

    # GET method → display stocks available to sell
    stocks = db.execute(
        """
        SELECT symbol,
               SUM(
                   CASE 
                       WHEN type = 'buy' THEN shares
                       WHEN type = 'sell' THEN -shares
                   END
               ) AS shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        HAVING shares > 0;
        """,
        user_id,
    )

    return render_template("sell.html", stocks=stocks)
