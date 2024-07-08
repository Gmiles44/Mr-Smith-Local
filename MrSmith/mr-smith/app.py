from cs50 import SQL
from flask_session import Session
import jinja2
from flask import Flask, flash, redirect, render_template, request, session
from helpers import login_required
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.secret_key = 'testing12345thesecret67890key'
db = SQL("sqlite:///game_data.db")


@app.route("/")
def index():
    return render_template("index.html")

#STATS STATS STATS STATS STATS
#STATS STATS STATS STATS STATS
#STATS STATS STATS STATS STATS
@app.route("/stats")
def stats():
    stats = db.execute("SELECT * FROM stats WHERE player_id = ?", session["user_id"])[0]
    return render_template("stats.html", stats=stats)

#REGISTER REGISTER REGISTER REGISTER
#REGISTER REGISTER REGISTER REGISTER
#REGISTER REGISTER REGISTER REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        passhash = generate_password_hash(password, method='scrypt', salt_length=16)
        if not name:
            flash("What the hell am I gonna call you? Give me a name!")
            return redirect("/register")
        elif not password:
            flash("Do you want just anyone to get in? Enter a password, ya dingus!")
            return redirect("/register")
        elif not password == confirm:
            flash("Typing the same thing twice too much a challenge? Try again, same one this time.")
            return redirect("/register")
        elif db.execute("SELECT * FROM users WHERE username = ?", name):
            flash("Sorry bud, name's already taken.")
            return redirect("/register")
        else:
            db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", name, passhash)
            rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
            session["user_id"] = rows[0]["id"]
            db.execute("INSERT INTO stats(player_id) VALUES (?)", session["user_id"])
            flash("Welcome in!")
            return redirect("/stats")

#LOGIN LOGIN LOGIN LOGIN LOGIN
#LOGIN LOGIN LOGIN LOGIN LOGIN
#LOGIN LOGIN LOGIN LOGIN LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if not request.form.get("username"):
            flash("Not gonna get in if you don't enter your username.")
            return redirect("/login")

        elif not request.form.get("password"):
            flash("You're just not going to enter your password? Do you want to get hacked?")
            return redirect("/login")

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("I hope you wrote your info down somewhere, cause one of those was wrong.")
            return redirect("/login")

        session.clear()
        session["user_id"] = rows[0]["id"]
        return redirect("/stats")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#CRAFT CRAFT CRAFT CRAFT CRAFT
#CRAFT CRAFT CRAFT CRAFT CRAFT
#CRAFT CRAFT CRAFT CRAFT CRAFT
@app.route("/craft", methods=["GET", "POST"])
def craft():
    recipes = db.execute("""SELECT c.name, c.base_price, IFNULL(ci.amount, 0) AS owned, m1.name AS m1_name, m1_amt, IFNULL(i1.amount, 0) AS i1_amt,
                            m2.name AS m2_name, m2_amt, IFNULL(i2.amount, 0) AS i2_amt,
                            m3.name AS m3_name, m3_amt, IFNULL(i3.amount, 0) AS i3_amt, c.id, level
                            FROM recipes
                            LEFT JOIN materials AS m1 ON recipes.m1_id = m1.id
                            LEFT JOIN materials_inventory AS i1 ON recipes.m1_id = i1.mat_id AND i1.player_id = ?
                            LEFT JOIN materials AS m2 ON recipes.m2_id = m2.id
                            LEFT JOIN materials_inventory AS i2 ON recipes.m2_id = i2.mat_id AND i2.player_id = ?
                            LEFT JOIN materials AS m3 ON recipes.m3_id = m3.id
                            LEFT JOIN materials_inventory AS i3 ON recipes.m3_id = i3.mat_id AND i3.player_id = ?
                            JOIN creations c ON recipes.creation_id = c.id
                            LEFT JOIN creations_inventory ci ON recipes.creation_id = ci.creation_id and ci.player_id = ?
                            ORDER BY c.base_price""", session["user_id"], session["user_id"], session["user_id"], session["user_id"])
    stats = db.execute("SELECT * FROM stats WHERE player_id = ?", session["user_id"])[0]
    if request.method == "GET":
        return render_template("craft.html", recipes=recipes, stats=stats)

    if request.method == "POST":
        id = request.form.get("id")
        materials = db.execute("""SELECT m1_id, m1_amt, m2_id, m2_amt, m3_id, m3_amt
                               FROM recipes WHERE creation_id = ?""", id)
        name = db.execute("SELECT name FROM creations WHERE id = ?", id)[0]['name']
        inventory = db.execute("""SELECT i1.amount AS mat1_amount,
                               i2.amount AS mat2_amount,
                               i3.amount AS mat3_amount
                               FROM recipes r
                               LEFT JOIN materials_inventory AS i1 ON i1.mat_id = r.m1_id AND i1.player_id = ?
                               LEFT JOIN materials_inventory AS i2 ON i2.mat_id = r.m2_id AND i2.player_id = ?
                               LEFT JOIN materials_inventory AS i3 ON i3.mat_id = r.m3_id AND i3.player_id = ?
                               WHERE r.creation_id = ?""", session["user_id"], session["user_id"], session["user_id"], id)
        if int(db.execute("SELECT energy FROM recipes WHERE creation_id = ?", id)[0]['energy']) > int(db.execute("SELECT energy FROM stats WHERE player_id = ?", session["user_id"])[0]['energy']):
            flash("Not enough energy!")
            return redirect("/craft")
        def craft_object():
            ids = []
            amounts = []
            for key, value in materials[0].items():
                if not value == None:
                    if key.endswith('_id'):
                        ids.append(value)
                    else:
                        amounts.append(value)
            for index, _id in enumerate(ids):
                db.execute("UPDATE materials_inventory SET amount = amount - ? WHERE mat_id = ? AND player_id = ?", amounts[index], _id, session["user_id"])
            if len(db.execute("SELECT * FROM creations_inventory WHERE creation_id = ? AND player_id = ?", id, session["user_id"])) == 0:
                db.execute("INSERT INTO creations_inventory (creation_id, amount, player_id) VALUES (?, 1, ?)", id, session["user_id"])
            else:
                db.execute("UPDATE creations_inventory SET amount = amount + 1 WHERE creation_id = ?", id)
            db.execute("UPDATE stats SET exp = exp + (SELECT exp FROM recipes WHERE creation_id = ?) WHERE player_id = ?", id, session["user_id"])
            db.execute("UPDATE stats SET energy = energy - (SELECT energy FROM recipes WHERE creation_id = ?) WHERE player_id = ?", id, session["user_id"])
            flash(f"Crafted {name}!")

        if inventory[0]['mat1_amount'] < materials[0]['m1_amt']:
            flash("Not enough materials!")
            return redirect("/craft")
        elif materials[0]['m2_amt']:
            if inventory[0]['mat2_amount'] < materials[0]['m2_amt']:
                flash("Not enough materials!")
                return redirect("/craft")
            elif materials[0]['m3_amt']:
                if inventory[0]['mat3_amount'] < materials[0]['m3_amt']:
                    flash("Not enough materials!")
                    return redirect("/craft")
                else:
                    craft_object()
            else:
                craft_object()
        else:
            craft_object()

        return redirect("/craft")

#INVENTORY INVENTORY INVENTORY INVENTORY
#INVENTORY INVENTORY INVENTORY INVENTORY
#INVENTORY INVENTORY INVENTORY INVENTORY
@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    stats = db.execute("SELECT * FROM stats WHERE player_id = ?", session["user_id"])[0]
    inventory = db.execute("""SELECT name, mi.amount, base_price
                           FROM materials m
                           JOIN materials_inventory mi
                           ON m.id = mi.mat_id
                           AND mi.player_id = ?""", session["user_id"])
    c_inventory = db.execute("""SELECT name, ci.amount, base_price
                             FROM creations c
                             JOIN creations_inventory ci
                             ON c.id = ci.creation_id
                             AND ci.player_id = ?""", session["user_id"])
    return render_template("inventory.html", inventory=inventory, stats=stats, c_inventory=c_inventory)

#MARKET MARKET MARKET MARKET MARKET
#MARKET MARKET MARKET MARKET MARKET
#MARKET MARKET MARKET MARKET MARKET
@app.route("/market", methods=["GET", "POST"])
def market():
    merchants = db.execute("""SELECT m.id, m.name, m1.id AS m1_id, m1.name AS m1_name, m1.base_price AS m1_base_price, inv_1_amt,
                        m2.id AS m2_id, m2.name AS m2_name, m2.base_price AS m2_base_price, inv_2_amt,
                        m3.id AS m3_id, m3.name AS m3_name, m3.base_price AS m3_base_price, inv_3_amt,
                        m4.id AS m4_id, m4.name AS m4_name, m4.base_price AS m4_base_price, inv_4_amt,
                        m5.id AS m5_id, m5.name AS m5_name, m5.base_price AS m5_base_price, inv_5_amt
                        FROM merchants m
                        LEFT JOIN materials m1 ON m1.id = m.inv_1
                        LEFT JOIN materials m2 ON m2.id = m.inv_2
                        LEFT JOIN materials m3 ON m3.id = m.inv_3
                        LEFT JOIN materials m4 ON m4.id = m.inv_4
                        LEFT JOIN materials m5 ON m5.id = m.inv_5""")
    inventory = db.execute("""SELECT i.amount, c.name, c.base_price, c.id FROM creations_inventory i
                            JOIN creations c ON c.id = i.creation_id AND i.player_id = ?""", session["user_id"])
    stats = db.execute("SELECT * FROM stats WHERE player_id = ?", session["user_id"])[0]

    if request.method == "GET":
        return render_template("market.html", merchants=merchants, stats=stats, inventory=inventory)

    if request.method == "POST":
        id = request.form.get("buy")
        amount = request.form.get("qty")
        total = int(request.form.get("total"))
        merch_id = request.form.get("id")
        m_number = int(request.form.get("m_number"))
        gold = int(db.execute("SELECT gold FROM stats WHERE player_id = ?", session["user_id"])[0]['gold'])
        if gold < total:
            flash("Not enough Gold!")
            return redirect("/market")
        elif len(db.execute("SELECT * FROM materials_inventory WHERE mat_id = ? AND player_id = ?", id, session["user_id"])) == 0:
            db.execute("INSERT INTO materials_inventory (mat_id, amount, player_id) VALUES (?, ?, ?)", id, amount, session["user_id"])
        else:
            db.execute("UPDATE materials_inventory SET amount = amount + ? WHERE mat_id = ? AND player_id = ?", amount, id, session["user_id"])
        db.execute("UPDATE merchants SET inv_?_amt = inv_?_amt - ? WHERE id = ?", m_number, m_number, amount, merch_id)
        db.execute("UPDATE stats SET gold = gold - ? WHERE player_id = ?", total, session["user_id"])
        db.execute("UPDATE merchants SET gold = gold + ?", total)
        return redirect("/market")

#SELL SELL SELL SELL SELL SELL SELL
#SELL SELL SELL SELL SELL SELL SELL
#SELL SELL SELL SELL SELL SELL SELL
@app.route("/sell", methods=["POST"])
def sell():
    id = request.form.get("sell")
    amount = request.form.get("qty")
    total = request.form.get("total")

    db.execute("UPDATE stats SET gold = gold + ? WHERE player_id = ?", total, session["user_id"])
    db.execute("UPDATE creations_inventory SET amount = amount - ? WHERE creation_id = ? AND player_id = ?", amount, id, session["user_id"])

    return redirect("/market")

#END_DAY END_DAY END_DAY END_DAY
#END_DAY END_DAY END_DAY END_DAY
#END_DAY END_DAY END_DAY END_DAY
@app.route("/end_day", methods=["GET"])
def end_day():
    stats = db.execute("SELECT * FROM stats WHERE player_id = ?", session["user_id"])[0]
    merchant_ids = db.execute("SELECT id FROM merchants")
    for id in merchant_ids:
        db.execute("""UPDATE merchants SET
                inv_1_amt = (SELECT ABS(RANDOM() % 7) + 6),
                inv_2_amt = (SELECT ABS(RANDOM() % 5) + 5),
                inv_3_amt = (SELECT ABS(RANDOM() % 4) + 4),
                inv_4_amt = (SELECT ABS(RANDOM() % 4) + 2),
                inv_5_amt = (SELECT ABS(RANDOM() % 3) + 1)
                WHERE id = ?""", id['id']
        )
    if stats['exp'] >= stats['next_level']:
        db.execute("UPDATE stats SET level = level + 1 WHERE player_id = ?", session["user_id"])
        db.execute("""UPDATE stats SET max_energy =
                   (SELECT max_energy FROM levels WHERE level =
                   (SELECT level FROM stats WHERE player_id = ?)),
                   next_level = (SELECT next_level FROM levels WHERE level = (
                   SELECT level FROM stats WHERE player_id = ?)) WHERE player_id = ?""", session["user_id"], session["user_id"], session["user_id"])
        db.execute("UPDATE stats SET exp = 0 WHERE player_id = ?", session["user_id"])
        db.execute("""UPDATE stats SET next_level = (SELECT experience FROM levels WHERE level = (
                   SELECT level FROM stats WHERE player_id = ?)) WHERE player_id = ?""", session["user_id"], session["user_id"])
        flash("Level up!")

    return redirect("/stats")

#TAVERN TAVERN TAVERN TAVERN TAVERN
#TAVERN TAVERN TAVERN TAVERN TAVERN
#TAVERN TAVERN TAVERN TAVERN TAVERN
@app.route("/tavern", methods=["GET", "POST"])
def tavern():

    if request.method == "GET":
        stats = db.execute("SELECT * FROM stats WHERE player_id = ?", session["user_id"])[0]
        food = db.execute("SELECT * FROM food WHERE 1")
        lodging = db.execute("SELECT * FROM lodging WHERE 1")
        return render_template("tavern.html", stats=stats, food=food, lodging=lodging)

    if request.method == "POST":
        energy = int(db.execute("SELECT energy FROM stats WHERE player_id = ?", session["user_id"])[0]['energy'])
        max_energy = int(db.execute("SELECT max_energy FROM stats WHERE player_id = ?", session["user_id"])[0]['max_energy'])
        gold = db.execute("SELECT gold FROM stats WHERE player_id = ?", session["user_id"])[0]['gold']

        if request.form.get("rent"):
            id = request.form.get("rent")
            price = db.execute("SELECT price FROM lodging WHERE id = ?", id)[0]['price']
            if gold < price:
                flash("I can't afford it!")
                return redirect("/tavern")
            if energy >= max_energy:
                flash("But I'm not tired!")
                return redirect("/tavern")
            db.execute("UPDATE stats SET gold = gold - (SELECT price FROM lodging WHERE id = ?) WHERE player_id = ?", id, session["user_id"])
            db.execute("UPDATE stats SET energy = energy + ROUND(max_energy * (SELECT recovery / 100 FROM lodging WHERE id = ?)) WHERE player_id = ?", id, session["user_id"])
            energy = int(db.execute("SELECT energy FROM stats WHERE player_id = ?", session["user_id"])[0]['energy'])
            if energy > max_energy:
                db.execute("UPDATE stats SET energy = max_energy WHERE player_id = ?", session["user_id"])
            return redirect("/end_day")

        else:
            id = request.form.get("buy")
            price = db.execute("SELECT price FROM food WHERE id = ?", id)[0]['price']
            if gold < price:
                flash("I can't even afford food!")
                return redirect("/tavern")
            if energy >= max_energy:
                flash("I couldn't eat another bite!")
                return redirect("/tavern")
            db.execute("UPDATE stats SET gold = gold - (SELECT price FROM food WHERE id = ?) WHERE player_id = ?", id, session["user_id"])
            db.execute("UPDATE stats SET energy = energy + (SELECT energy FROM food WHERE id = ?) WHERE player_id = ?", id, session["user_id"])
            energy = db.execute("SELECT energy FROM stats WHERE player_id = ?", session["user_id"])[0]['energy']
            if energy > max_energy:
                db.execute("UPDATE stats set energy = max_energy WHERE player_id = ?", session["user_id"])
            return redirect("/tavern")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)