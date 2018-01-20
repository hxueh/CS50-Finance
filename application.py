from pymysql import cursors, connect
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from decimal import Decimal

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Check the user_id
    if 'user_id' in session:
        user = session["user_id"]
    else:
        return apology("Must login")
    
    # Connect to database
    cnx = connect(host = 'localhost', user = 'root', db = 'cs50_finance')
    db = cnx.cursor()

    # Get my money and my username
    db.execute("SELECT * FROM `users` WHERE id = %s;", (user,))
    my_row = db.fetchone()
    remaining_money = my_row[3]

    # Show my portfolio I own now
    # db.execute("CREATE TABLE IF NOT EXISTS portfolio (transit_id INTEGER PRIMARY KEY AUTO_INCREMENT, symbol TEXT, shares INTEGER, time TEXT, price NUMERIC, Action TEXT, buyer INT UNSIGNED, FOREIGN KEY (buyer) REFERENCES users (id))")
    db.execute("SELECT `symbol` FROM `portfolio` WHERE `buyer` = %s", (user,))
    portfolio_list = db.fetchall()

    # Use set type to store stock I own
    stock_I_ownd = set()
    for i in portfolio_list:
        stock_I_ownd.add(i[0])

    # Create a dictionary to store stock-shares, where key is stock and value is shares
    stock_shares_dict = {}
    for single_stock in stock_I_ownd:
        db.execute("SELECT * FROM `portfolio` WHERE `buyer` = %s AND `symbol` = %s", (user, single_stock))
        one_stock = db.fetchall()
        stock_shares_dict[single_stock] = 0
        for i in range(len(one_stock)):
            if one_stock[i][5] == 'Buy':
                stock_shares_dict[single_stock] += one_stock[i][2]
            elif one_stock[i][5] == 'Sell':
                stock_shares_dict[single_stock] -= one_stock[i][2]

    # To avoid "RuntimeError: dictionary changed size during iteration", create a list of dictionary key and if the value is 0, delete it
    for key in list(stock_shares_dict):
        if stock_shares_dict[key] == 0:
            del stock_shares_dict[key]

    # Update stock_shares_dict to store symbol, name, shares, current price and price * shares
    for key in list(stock_shares_dict):
        share = stock_shares_dict[key]
        info = lookup(key)
        stock_shares_dict[key] = [key, info["name"], share, usd(info["price"]), usd(share * info["price"])]

    # My money, cash + stock
    capital = remaining_money
    for key in list(stock_shares_dict):
        capital += Decimal(stock_shares_dict[key][4][1:].replace(',', '').strip('\''))

    db.close()
    cnx.close()

    return render_template("index.html", stock_shares_dict = stock_shares_dict, remaining_money = usd(remaining_money), capital = usd(capital))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing symbol")
        elif not request.form.get("shares"):
            return apology("Missing shares")
        elif not lookup(request.form.get("symbol")):
            return apology("Invalid symbol")

        # check if shares is number
        try:
            int(request.form.get("shares"))
        except:
            return apology("Wrong type")

        if int(request.form.get("shares")) < 0:
            return apology("Shares must bigger than 0")

        # Must login
        if 'user_id' in session:
            user = session["user_id"]
        else:
            return apology("Must login")

        cnx = connect(host = 'localhost', user = 'root', db = 'cs50_finance', autocommit = True)
        db = cnx.cursor()

        # Remember the user via user's id and save it's name and money
        db.execute("SELECT * FROM `users` WHERE id = %s", (user,))
        my_row = db.fetchone()
        money = my_row[3]

        # Check if we can afford
        price = lookup(request.form.get("symbol"))["price"]
        worth = price * request.form.get("shares")
        if money < worth:
            return apology("Can't afford")

        # Check if the portfolio database exists, if not, create one
        # db.execute("CREATE TABLE IF NOT EXISTS \"portfolio\" (\"Transit_id\" INTEGER PRIMARY KEY AUTOINCREMENT, \"Symbol\" TEXT, \"Shares\" INTEGER, \"Time\" TEXT, \"Price\" NUMERIC, \"Action\" TEXT, \"Buyer\" TEXT, FOREIGN KEY (\"Buyer\") REFERENCES \"users\" (\"username\"));")

        # Record time and accurate to second
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert data into database, with user, stock, shares and time
        db.execute("INSERT INTO `portfolio` (`symbol`, `shares`, `time`, `price`, `action`, `buyer`) VALUES (%s, %s, %s, %s, %s, %s)", (request.form.get("symbol"), request.form.get("shares"), now, price, 'Buy', user))

        # If all the above success, then update cash
        db.execute("UPDATE `users` SET cash = (cash - %s) WHERE id = %s", (worth, user))

        db.close()
        cnx.close()

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Check the user_id
    if 'user_id' in session:
        user = session["user_id"]
    else:
        return apology("Must login")
    
    # Connect to database
    cnx = connect(host = 'localhost', user = 'root', db = 'cs50_finance')
    db = cnx.cursor()

    # Store my exchange history
    db.execute("SELECT * FROM `portfolio` WHERE `buyer` = %s", (user, ))

    # db.fetchall will create a tuple containing tuple, which don't support item assignment
    # convert to list to modify
    history, temp = [], db.fetchall()
    for g in temp:
        history.append(list(g))
    for t in history:
        t[4] = usd(t[4])

    # Disconnect
    db.close()
    cnx.close()

    return render_template("history.html", history = history)


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

        # Start checking
        # Connect to the database first
        cnx = connect(host = 'localhost', user = 'root', db = 'cs50_finance')
        db = cnx.cursor()

        # Query database for username
        db.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username"),))
        rows = db.fetchone()

        # Ensure username exists and password is correct
        if len(rows) == 0 or not check_password_hash(rows[2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]

        # Disconnect from the database
        db.close()
        cnx.close()

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
    return redirect("/login")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # There are two ways of submitting
    # If the submitting method is "POST"
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("Missing symbol")

        stock = lookup(request.form.get("symbol"))

        if not stock:
            return apology("Invalid symbol")

        # Ensure the format
        stock["price"] = usd(stock["price"])

        return render_template("quoted.html", stock = stock)

    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Missing username")

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("Missing password")

        # Generater password hash
        password_hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # Ensure confirmation was submitted and be the same as password
        if (not request.form.get("confirmation")) or (not check_password_hash(password_hash, request.form.get("confirmation"))):
            return apology("Password don't match")

        # Connect to the database
        cnx = connect(host = 'localhost', user = 'root', db = 'cs50_finance', autocommit = True)
        db = cnx.cursor()

        # Ensure username was not been taken
        result = db.execute("SELECT * FROM `users` WHERE `username` = %s", (request.form.get("username"),))
        if result:
            return apology("USERNAME TAKEN")

        db.execute("INSERT INTO `users` (`username`, `hash`) VALUES(%s, %s);", (request.form.get("username"), password_hash))

        # Choose the user
        db.execute("SELECT * FROM `users` WHERE username = %s", (request.form.get("username"), ))
        rows = db.fetchone()

        # And login
        session["user_id"] = rows[0]

        # Disconnect from the database
        cnx.close()
        db.close()

        return redirect("/")

    else:
        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Check the user_id
    if 'user_id' in session:
        user = session["user_id"]
    else:
        return apology("Must login")

    # Connect to the database
    cnx = connect(host = 'localhost', user = 'root', db = 'cs50_finance', autocommit = True)
    db = cnx.cursor()

    # Remember the user via user's id and save it's name and money
    db.execute("SELECT * FROM `users` WHERE id = %s", (user, ))
    my_row = db.fetchone()
    money = my_row[3]

    # Show my portfolio I own now
    db.execute("SELECT `symbol` FROM `portfolio` WHERE `buyer` = %s;", (user, ))
    portfolio_list = db.fetchall()

    # Use set type to store stock I ownd
    stock_I_ownd = set()
    for i in portfolio_list:
        stock_I_ownd.add(i[0])

    # Create a dictionary to store stock-shares, where key is stock and value is shares
    stock_shares_dict = {}
    for single_stock in stock_I_ownd:
        db.execute("SELECT * FROM `portfolio` WHERE `buyer` = %s AND `symbol` = %s", (user, single_stock))
        one_stock = db.fetchall()
        stock_shares_dict[single_stock] = 0
        for i in range(len(one_stock)):
            if one_stock[i][5] == 'Buy':
                stock_shares_dict[single_stock] += one_stock[i][2]
            elif one_stock[i][5] == 'Sell':
                stock_shares_dict[single_stock] -= one_stock[i][2]

    # To avoid "RuntimeError: dictionary changed size during iteration", create a list of dictionary key and if the value is 0, delete it
    for key in list(stock_shares_dict):
        if stock_shares_dict[key] == 0:
            del stock_shares_dict[key]

    # Create a list to store stocks that are not be sold out
    listofstock = []
    for key in list(stock_shares_dict):
        listofstock.append(key)
        
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing symbol")
        elif not request.form.get("shares"):
            return apology("Missing shares")

        # If the shares the user type in is greater than the shares you own, return an apology
        if int(request.form.get("shares")) > stock_shares_dict[request.form.get("symbol")]:
            return apology("Too many shares")

        # Record time and accurate to second
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute("INSERT INTO `portfolio` (`symbol`, `shares`, `time`, `price`, `action`, `buyer`) VALUES (%s, %s, %s, %s, %s, %s);", (request.form.get("symbol"), request.form.get("shares"), now, lookup(request.form.get("symbol"))["price"], 'Sell', user))
        
        # Update the cash I own now
        worth = float(float(lookup(request.form.get("symbol"))["price"]) * int(request.form.get("shares")))
        db.execute("UPDATE `users` SET `cash` = (cash + %s) WHERE `id` = %s", (worth, user))

        # Close connection
        db.close()
        cnx.close()

        return redirect("/")

    else:
        return render_template("sell.html", listofstock = listofstock)

@app.route("/password", methods=["GET", "POST"])
@login_required
def password_changing():
    if request.method == "POST":
        if not request.form.get("password"):
            return apology("Missing password")

        # Check the user_id
        if 'user_id' in session:
            user = session["user_id"]
        else:
            return apology("Must login")

        # Generate password hash
        password_hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # If password confirmation was not submitted or doesn't match
        if (not request.form.get("confirmation")) or (not check_password_hash(password_hash, request.form.get("confirmation"))):
            return apology("Password don't match")

        # Connect to database
        cnx = connect(host = 'localhost', user = 'root', db = 'cs50_finance', autocommit = True)
        db = cnx.cursor()

        # Update the password hash in database
        db.execute("UPDATE users SET hash = %s WHERE id = %s", (password_hash, user))

        db.close()
        cnx.close()

        return redirect("/")

    else:
        return render_template("password.html")

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run()