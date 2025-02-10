import os
import datetime
from flask import Flask, flash, redirect, render_template, request, session, g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd, get_stock_chart
from database import close_db, initialize_database, execute_query

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize database
initialize_database()

# Ensure database connections close properly
@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)

# Prevent browsers from caching responses
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

    # user_id variable for later use
    user_id = session["user_id"]

    # Get stock tickers and the amount of stocks owned by this user
    stocks = execute_query("""SELECT b.stock_bought AS stock_owned,
                                SUM(b.amount_bought) - COALESCE(s.total_sold, 0) AS amount_owned
                            FROM stock_buys b
                            LEFT JOIN (
                                SELECT stock_sold, SUM(amount_sold) AS total_sold, user_id
                                FROM stock_sells
                                GROUP BY stock_sold, user_id
                            ) s ON b.stock_bought = s.stock_sold AND b.user_id = s.user_id
                            WHERE b.user_id = ?
                            GROUP BY b.stock_bought
                            HAVING amount_owned > 0""", (user_id,))

    # Populate current prices dictionary to get up to date prices for the stocks user owns
    current_prices = {}
    for stock in range(len(stocks)):
        quote = lookup(stocks[stock]["stock_owned"])
        current_prices[stocks[stock]["stock_owned"]] = quote["price"]

    # Find out how much cash user has
    cash = execute_query("SELECT cash FROM users WHERE id = ?", (user_id,))

    # Calculate how much currently owned stocks by user are worth in current prices
    sum_total = sum(stock["amount_owned"] * current_prices[stock["stock_owned"]] for stock in stocks)

    return render_template("index.html", stocks=stocks, current_prices=current_prices, cash=cash, sum_total=sum_total)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        username = request.form.get("username")
        rows = execute_query("SELECT * FROM users WHERE username = ?", (username,))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Do this if user accesses page with POST method
    if request.method == "POST":
        # Get inputs from user
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Look for username in database
        rows = execute_query("SELECT * FROM users WHERE username = ?", (username,))

        # Check whether user provided username
        if not username:
            return apology("must provide username", 400)
        # Check whether username already exists in database
        elif len(rows) != 0:
            return apology("username already exists", 400)
        # Check whether password is provided
        if not password:
            return apology("must enter password", 400)
        # Check whether password confirmation is provided
        elif not confirmation:
            return apology("must re-enter password", 400)
        # Check whether password and password confirmation matches
        elif password != confirmation:
            return apology("passwords do not match", 400)

        # Generate hash of the password
        passhash = generate_password_hash(password)

        # Store user in database
        execute_query("INSERT INTO users (username, hash) VALUES (?, ?)", (username, passhash))

        # Store id in session now that user is registered
        id = execute_query("SELECT id FROM users WHERE username=?", (username,))        
        session["user_id"] = id[0]["id"]

        flash("Thanks for registering! Now you are logged in.")
        return redirect("/")

    # If user arrives to page with GET method
    else:
        return render_template("register.html")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # Do this if user accesses page with POST method
    if request.method == "POST":
        # Get inputs from user
        quote = request.form.get("symbol").upper()

        # Check whether user entered quote
        if not quote:
            return apology("Must enter a quote", 400)

        # Get quote for user's stock
        stock = lookup(quote)

        # Check whether stock is found
        if not stock:
            return apology("no such stock found", 400)

        # Variables from stock quote
        name = stock["name"]
        price = stock["price"]
        symbol = stock["symbol"]

        chart = get_stock_chart(symbol)

        # If quote is available we render info
        return render_template("quoted.html", name=name, price=price, symbol=symbol, chart=chart)

    else:
        # If method is GET we render quote page
        return render_template("quote.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # Do this if user accesses page with POST method
    if request.method == "POST":
        # Get input provided by user
        symbol = request.form.get("symbol").upper()
        # Get current quote for the stock user wants to buy
        quote = lookup(symbol)
        # Get user id
        user_id = session["user_id"]

        # Check whether user provided symbol
        if not symbol:
            return apology("Must provide stock symbol", 400)
        # Check whether stock provided exists
        elif not quote:
            return apology("No such stock found", 400)

        # Get shares input and check whether it is valid number
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Number of shares have to be a valid number", 400)

        # Check whether user provided a positive number of shares
        if int(shares) <= 0:
            return apology("the number of shares must be more than 0", 400)

        # Get how much cash user has
        usercash = execute_query("SELECT cash FROM users WHERE id=?", (user_id,))

        # Check whether user has enough cash to complete purchase
        if float(shares * quote["price"]) > float(usercash[0]["cash"]):
            return apology("There is not enough cash to complete this purchase", 400)

        # Add stock buy into database
        execute_query("INSERT INTO stock_buys (time_bought, stock_bought, price_bought, amount_bought, user_id) VALUES (?, ?, ?, ?, ?)",
                   (datetime.datetime.now(), symbol, quote["price"], shares, user_id))

        # Update user cash after completing purchase
        execute_query("UPDATE users SET cash = ? WHERE id = ?", (usercash[0]["cash"] - shares * quote["price"], user_id))

        # When transaction is successful redirect to index and flash message
        flash("Bought!")
        return redirect("/")

    return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # user_id variable for later use
    user_id = session["user_id"]

    # Get all the stock user owns and the amounts owned
    stocks_owned = execute_query("""SELECT b.stock_bought AS stock_owned,
                            SUM(b.amount_bought) - COALESCE(s.total_sold, 0) AS amount_owned
                        FROM stock_buys b
                        LEFT JOIN (
                            SELECT stock_sold, SUM(amount_sold) AS total_sold, user_id
                            FROM stock_sells
                            GROUP BY stock_sold, user_id
                        ) s ON b.stock_bought = s.stock_sold AND b.user_id = s.user_id
                        WHERE b.user_id = ?
                        GROUP BY b.stock_bought
                        HAVING amount_owned > 0""", (user_id,))

    # Do this if user accesses page with POST method
    if request.method == "POST":
        # Get user inputs from these fields
        user_stock = request.form.get("symbol").upper()
        stock_amount = request.form.get("shares")

        # Check whether user provided a stock ticker
        if not user_stock:
            return apology("Must select a stock to sell", 400)

        # Check whether stock ticker provided exists in user's owned stocks
        stock_exists = False
        amount_owned = 0
        for stock in stocks_owned:
            if stock["stock_owned"] == user_stock:
                stock_exists = True
                amount_owned = stock["amount_owned"]
                break
        if stock_exists == False:
            return apology("User doesn't own this stock", 400)

        # Check whether user provided a positive number for amount
        if int(stock_amount) < 0:
            return apology("The number of stocks to sell should be positive", 400)

        # Check whether user owns this many stocks
        if int(stock_amount) > amount_owned:
            return apology("You don't have enough stocks to sell", 400)

        # Sell the stocks
        quote = lookup(user_stock)
        execute_query("INSERT INTO stock_sells (time_sold, stock_sold, price_sold, amount_sold, user_id) VALUES (?, ?, ?, ?, ?)",
                    (datetime.datetime.now(), user_stock, quote["price"], stock_amount, user_id))

        # Update cash for user
        current_cash = execute_query("SELECT cash FROM users WHERE id = ?", (user_id,))
        execute_query("UPDATE users SET cash = ? WHERE id = ?", (float(current_cash[0]["cash"]) + float(quote["price"]) * float(stock_amount), user_id))

        flash("Sold!")
        return redirect("/")

    return render_template("sell.html", stocks_owned=stocks_owned)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # user_id variable for later use
    user_id = session["user_id"]

    # Get combined transactions from buys and sells from database
    transactions = execute_query("""SELECT time, ticker, price, amount, user_id, transaction_type
                              FROM (
                                SELECT time_bought AS time, stock_bought AS ticker, price_bought AS price,
                                amount_bought AS amount, user_id, 'BOUGHT' AS transaction_type
                                FROM stock_buys
                                WHERE user_id = ?

                                UNION ALL

                                SELECT time_sold AS time, stock_sold AS ticker, price_sold AS price,
                                amount_sold AS amount, user_id, 'SOLD' AS transaction_type
                                FROM stock_sells
                                WHERE user_id = ?
                              ) AS combined_stocks
                              ORDER BY time;""", (user_id, user_id))
    
    # Convert to datetime object
    transactions = [dict(transaction) for transaction in transactions]
    for transaction in transactions:
        transaction["time"] = datetime.datetime.strptime(transaction["time"], "%Y-%m-%d %H:%M:%S.%f")

    return render_template("history.html", transactions=transactions)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Change profile settings"""

    # user_id variable for later use
    user_id = session["user_id"]

    username = execute_query("SELECT username FROM users WHERE id = ?", (user_id,))[0]["username"]

    # Do this if page was accessed through POST method
    if request.method == "POST":
        # Request to change username
        if request.form.get("form") == "form1":
            # Get new username input from user
            new_username = request.form.get("new_username")

            # Look for username in database
            rows = execute_query("SELECT * FROM users WHERE username = ?", (new_username,))

            # Check whether user entered a new username
            if not new_username:
                return apology("Must provide username", 400)

            # Check whether username alrady exists in database
            elif len(rows) != 0:
                return apology("Username already exists", 400)

            # Change username
            execute_query("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))

            flash("Succesfully changed username!")
            return redirect("/profile")

        elif request.form.get("form") == "form2":
            # Get user inputs
            old_password = request.form.get("old_password")
            new_password = request.form.get("new_password")
            conf_password = request.form.get("conf_password")

            # Check whether usern entered all password input fields
            if not (old_password and new_password and conf_password):
                return apology("Must enter all password fields", 400)

            # Check whether new password and password confirmation match
            if new_password != conf_password:
                return apology("Re-entered password doesn't match new password", 400)

            # Check whether old password is correct
            database_hash = execute_query("SELECT hash FROM users WHERE id = ?", (user_id,))[0]["hash"]
            if not check_password_hash(database_hash, old_password):
                return apology("Old password is incorrect", 400)

            # Change password
            passhash = generate_password_hash(new_password)
            execute_query("UPDATE users SET hash = ? WHERE id = ?", (passhash, user_id))

            flash("Succesfully changed password!")
            return redirect("/profile")

    return render_template("profile.html", username=username)


if __name__ == "__main__":
    app.run(debug=True)