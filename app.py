from flask import Flask, render_template, request, jsonify,redirect,url_for,session,flash
import sqlite3
from datetime import datetime



app = Flask(__name__)
DB_FILE = 'auction_platform.db'
app.secret_key = 'Kavana'



# 🛠 DB Connection Helper
def get_db():
    conn = sqlite3.connect('auction_platform.db')
    conn.row_factory = sqlite3.Row
    return conn

conn = sqlite3.connect('auction_platform.db')
cursor = conn.cursor()
def query_db(query, args=(), one=False):
    with sqlite3.connect('auction_platform.db') as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(query, args)
        result = cur.fetchall()
        return (result[0] if result else None) if one else [dict(row) for row in result]

@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html') 
@app.route("/view_users")
def view_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM USERS").fetchall()
    conn.close()
    
    output = ""
    for user in users:
        output += f"ID: {user['user_id']}, Name: {user['name']}, Email: {user['email']}<br>"
    
    return output
conn = get_db()
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS TEMP_USERS (
    temp_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
''')
conn.commit()
conn.close()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

       
        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('help'))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERS WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        # Check if email exists in TEMP_USERS
        cursor.execute("SELECT * FROM TEMP_USERS WHERE email = ?", (email,))
        existing_temp_user = cursor.fetchone()

        if existing_user or existing_temp_user:
            flash("Email already exists. Please log in or use a different email.")
            return redirect(url_for('signup'))
        cursor.execute("INSERT INTO TEMP_USERS (name, email, password) VALUES (?, ?, ?)", 
                         (name, email, password))  # For security, hash this in real apps
        conn.commit()
        cursor.execute("SELECT temp_user_id FROM TEMP_USERS WHERE email = ?", (email,))
        # After successful signup, fetch the new temp_user_id
        cursor.execute("SELECT temp_user_id FROM TEMP_USERS WHERE email = ?", (email,))
        new_user = cursor.fetchone()
        new_user_id = new_user["temp_user_id"]

# Just to be safe: Clear any accidental bids or wins tied to this ID
        cursor.execute("DELETE FROM BIDS WHERE user_id = ?", (new_user_id,))
        cursor.execute("DELETE FROM AUCTION_WINNERS WHERE user_id = ?", (new_user_id,))
        conn.commit()

        #user_id = cursor.fetchone()['temp_user_id']
        session['email'] = email
        session['user_id'] = user_id
        session['user_type'] = 'temp'
        session['logged_in'] = True

        flash("Signup successful. Please login.")
        return redirect(url_for('profile'))
       

    return render_template('signup.html')
  

# 🔐 Login route
@app.route('/login', methods=['GET', 'POST'])  # ✅ without trailing slash
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERS WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user and user["password"] == password:
            session['email'] = user['email']
            session['user_id'] = user['user_id']
            session['user_type'] = 'db'
            session['logged_in'] = True
            return redirect(url_for('profile'))

        # Check TEMP_USERS table
        cursor.execute("SELECT * FROM TEMP_USERS WHERE email = ?", (email,))
        temp_user = cursor.fetchone()

        if temp_user and temp_user["password"] == password:
            session['email'] = temp_user['email']
            session['user_id'] = temp_user['temp_user_id']
            session['user_type'] = 'temp'
            session['logged_in'] = True
            return redirect(url_for('profile'))
   
        flash("Invalid email or password.")
        return redirect(url_for('signup'))
    
    
    return render_template("login.html")


@app.route('/profile', methods=["GET"])
def profile():
    print("SESSION:", session)

    if 'email' not in session or 'user_type' not in session:
        
        flash("You must be logged in to view your profile.")
        return redirect(url_for('login'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    email = session['email']
    user_type = session.get('user_type', 'db')  # Default to 'db' if not set

    if user_type == 'temp':
        cursor.execute("SELECT temp_user_id AS user_id, name, email FROM TEMP_USERS WHERE email = ?", (email,))
    else:
        cursor.execute("SELECT user_id, name, email FROM USERS WHERE email = ?", (email,))

    user = cursor.fetchone()
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))

    user_id = user['user_id']

    # Bid history
    cursor.execute("""
        SELECT I.name AS item_name, B.bid_amount, B.bid_time
        FROM BIDS B
        JOIN AUCTIONS A ON B.auction_id = A.auction_id
        JOIN ITEMS I ON A.item_id = I.item_id
        WHERE B.user_id = ?
        ORDER BY B.bid_time DESC
    """, (user_id,))
    bids = cursor.fetchall()


    # Get won auctions
    if session['user_type'] == 'temp':
        cursor.execute("""
            SELECT DISTINCT
                A.auction_id,
                AW.winning_bid,
                CASE 
                    WHEN AW.payment_id IS NOT NULL THEN 'Paid'
                    ELSE 'Not Paid'
                END AS payment_status
            FROM AUCTIONS A
            JOIN AUCTION_WINNERS AW ON A.auction_id = A.item_id
            WHERE AW.user_id = ?
        """, (user_id,))
    else:
        cursor.execute("""
        SELECT DISTINCT
            I.name AS item_name, 
            AW.winning_bid,
            CASE 
                WHEN AW.payment_id IS NOT NULL THEN 'Paid'
                ELSE 'Not Paid'
            END AS payment_status
        FROM AUCTIONS A
        JOIN AUCTION_WINNERS AW ON A.auction_id = A.item_id
        JOIN ITEMS I ON A.item_id = I.item_id
        WHERE AW.user_id = ?
    """, (user_id,))
    won_auctions = cursor.fetchall()

    conn.close()

    return render_template('profile.html', name=user["name"], email=user["email"], bids=bids, won_auctions=won_auctions)


@app.route('/logout')
def logout():
    session.clear()  # Clears all session data (logs the user out)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

conn = sqlite3.connect('auction_platform.db')
cursor = conn.cursor()

# Step 1: Clear existing bids and winner assignments
cursor.execute("DELETE FROM AUCTION_WINNERS")
cursor.execute("UPDATE AUCTIONS SET winner_id = NULL WHERE winner_id IS NOT NULL")


# Step 2: Create realistic diverse bid data
now = datetime.now().isoformat()
bids = [
    (1, 1, 1600.00),  # auction 1 won by user 1
    (1, 2, 1500.00),
    
    (2, 3, 1700.00),  # auction 2 won by user 3
    (2, 4, 1600.00),

    (5,4,1000.00),
    (5,2,1045.00)
]

# Step 3: Insert dummy bids

conn.commit()

# Step 4: Assign winners to auctions that are completed and item_id < 34
cursor.execute('''
    SELECT A.auction_id, A.item_id, MAX(B.bid_amount) AS max_bid
    FROM AUCTIONS A
    JOIN BIDS B ON A.auction_id = B.auction_id
    WHERE A.status = 'completed' AND A.item_id < 34
    GROUP BY A.auction_id
''')

auctions = cursor.fetchall()

for auction_id, item_id, winning_bid in auctions:
    cursor.execute('''
        SELECT user_id FROM BIDS
        WHERE auction_id = ? AND bid_amount = ?
        LIMIT 1
    ''', (auction_id, winning_bid))
    user_result = cursor.fetchone()
    
    if user_result:
        user_id = user_result[0]
        
        # Insert into AUCTION_WINNERS
        cursor.execute('''
            INSERT INTO AUCTION_WINNERS (user_id, winning_bid)
            VALUES (?, ?)
        ''', (user_id, winning_bid))
        
        winner_id = cursor.lastrowid

        # Update AUCTIONS table with winner_id
        cursor.execute('''
            UPDATE AUCTIONS SET winner_id = ? WHERE auction_id = ?
        ''', (winner_id, auction_id))

conn.commit()
conn.close()





          

@app.route("/pay/<int:auction_id>/gateway", methods=["GET", "POST"])
def payment_gateway(auction_id):
    conn = get_db()
    
    # Get auction details with winning bid and user ID
    auction = conn.execute("""
        SELECT 
            A.auction_id,
            MAX(B.bid_amount) AS winning_bid,
            B.user_id
        FROM 
            AUCTIONS A
        JOIN 
            BIDS B ON A.auction_id = B.auction_id
        WHERE 
            A.auction_id = ?
        GROUP BY 
            A.auction_id
    """, (auction_id,)).fetchone()

    if not auction:
        conn.close()
        flash("Auction not found.")
        return redirect(url_for('profile'))

    if request.method == "POST":
        # Insert into PAYMENT table
        cursor = conn.execute("""
            INSERT INTO PAYMENT (amount, payment_date, user_id) 
            VALUES (?, datetime('now'), ?)
        """, (auction["winning_bid"], auction["user_id"]))
        payment_id = cursor.lastrowid

        # Update AUCTION_WINNERS with the new payment ID
        conn.execute("""
            UPDATE AUCTION_WINNERS 
            SET payment_id = ? 
            WHERE user_id = ? AND winning_bid = ?
        """, (payment_id, auction["user_id"], auction["winning_bid"]))

        conn.commit()
        conn.close()
        
        return redirect(url_for('profile'))

    conn.close()
    return render_template("payment_gateway.html", 
                           auction_id=auction["auction_id"], 
                           amount=auction["winning_bid"])


conn = get_db()
auction = conn.execute("SELECT * FROM auctions WHERE auction_id = ?", (auction_id,)).fetchone()
print(dict(auction))  # Debug line


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check in USERS
        cursor.execute("SELECT * FROM USERS WHERE email = ?", (email,))
        user = cursor.fetchone()

        # If not found, check TEMP_USERS
        if not user:
            cursor.execute("SELECT * FROM TEMP_USERS WHERE email = ?", (email,))
            user = cursor.fetchone()

        if user:
            session['reset_email'] = email  # store email temporarily
            flash("Email verified. Please reset your password.")
            return redirect(url_for('reset_password'))
        else:
            flash("No account found with that email.")
            return redirect(url_for('forgot_password'))

    return render_template("set_password.html")






@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        flash("Unauthorized access to password reset.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('reset_password'))

        email = session['reset_email']
        conn = get_db()
        cursor = conn.cursor()

        # First try USERS
        cursor.execute("SELECT * FROM USERS WHERE email = ?", (email,))
        if cursor.fetchone():
            cursor.execute("UPDATE USERS SET password = ? WHERE email = ?", (new_password, email))
        else:
            cursor.execute("UPDATE TEMP_USERS SET password = ? WHERE email = ?", (new_password, email))

        conn.commit()
        conn.close()
        session.pop('reset_email', None)

        flash("Password updated successfully. Please login.")
        return redirect(url_for('login'))

    return render_template("set_password.html")

  

  
@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT user_id, name, email, role FROM USERS WHERE user_id=?", (user_id,)).fetchone()
    conn.close()

    if user:
        return jsonify(dict(user)), 200
    return jsonify({"error": "User not found ❌"}), 404


# 📂 List all users (for admin/testing)
@app.route('/users', methods=['GET'])
def list_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM USERS").fetchall()
    conn.close()
    return jsonify([dict(user) for user in users]), 200




@app.route('/items', methods=['GET'])
def get_items():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ITEMS.*, CATEGORIES.name, ITEM_PHOTOS.photo_url
        FROM ITEMS
        LEFT JOIN CATEGORIES ON ITEMS.category_id = CATEGORIES.category_id
        LEFT JOIN ITEM_PHOTOS ON ITEMS.photo_id = ITEM_PHOTOS.photo_id
    """)
    items = cursor.fetchall()
    conn.close()

    return jsonify([dict(item) for item in items]), 200





# Route to fetch active auctions
@app.route('/get_active_auctions', methods=['GET'])
def get_active_auctions():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = '''
        SELECT A.*, I.name, I.description, I.condition, I.category_id, I.photo_url
        FROM AUCTIONS A
        JOIN ITEMS I ON A.item_id = I.item_id
        WHERE A.status = 'active'
        AND A.item_id <= 34
        AND I.photo_url IS NOT NULL
        AND I.photo_url != ''
    '''

    auctions = cursor.execute(query).fetchall()
    conn.close()

    result = [dict(auction) for auction in auctions]
    return jsonify(result), 200

@app.route('/auctions', methods=['GET', 'POST'])
def show_auctions():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        if 'email' not in session:
            flash('Please log in to place a bid.')
            return redirect(url_for('login'))

        auction_id = request.form.get('auction_id')
        bid_amount = request.form.get('bid_amount')

        if not bid_amount:
            flash('Bid amount is required.')
            return redirect(url_for('auctions'))

        try:
            bid_amount = float(bid_amount)
        except ValueError:
            flash('Invalid bid amount.')
            return redirect(url_for('auctions'))

        user_id = session.get('user_id')
        user_email = session.get('email', 'Guest')

        # Save the bid
        cursor.execute(
            "INSERT INTO BIDS (auction_id, bid_amount, user_id, bid_time) VALUES (?, ?, ?, datetime('now'))",
            (auction_id, bid_amount, user_id)
        )
        conn.commit()
        flash('Your bid has been placed!')

    query = '''
        SELECT A.*, I.name, I.description, I.photo_url, A.starting_price, A.end_date
        FROM AUCTIONS A
        JOIN ITEMS I ON A.item_id = I.item_id
        WHERE A.status = 'active'
        AND A.item_id <= 34
    '''
    auctions = cursor.execute(query).fetchall()
    conn.close()

    user_email = session.get('email', 'Guest')

    return render_template("auctions.html", auctions=auctions, user_email=user_email)


    


@app.route('/place_bid', methods=['POST'])
def place_bid():
    user_id = session.get('user_id')
    auction_id = request.form['auction_id']
    bid_amount = request.form['bid_amount']

    conn = sqlite3.connect('auction_platform.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO BIDS (user_id, auction_id, bid_amount, bid_time)
        VALUES (?, ?, ?, datetime('now'))
    ''', (user_id, auction_id, bid_amount))

    conn.commit()
    conn.close()

    return redirect('/auctions')  # or return JSON if using JS
  


    
       

@app.route('/bids', methods=['GET'])
def get_bids():
    bids = query_db('SELECT * FROM BIDS')
    return jsonify(bids)


def assign_winners():
    conn = sqlite3.connect('auction_platform.db')
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    # ✅ 1. Get auctions that have ended, have no winner, and item_id < 34
    cursor.execute('''
        SELECT auction_id FROM AUCTIONS
        WHERE end_date <= ? AND winner_id IS NULL AND item_id <= 34
    ''', (now,))
    ended_auctions = cursor.fetchall()

    for (auction_id,) in ended_auctions:
        # ✅ 2. Get highest bid for this auction
        cursor.execute('''
            SELECT user_id, MAX(bid_amount) FROM BIDS
            WHERE auction_id = ?
        ''', (auction_id,))
        result = cursor.fetchone()
        user_id, winning_bid = result

        if user_id is not None:
            # ✅ 3. Insert into AUCTION_WINNERS
            cursor.execute('''
                INSERT INTO AUCTION_WINNERS (user_id, winning_bid)
                VALUES (?, ?)
            ''', (user_id, winning_bid))
            winner_id = cursor.lastrowid

            # ✅ 4. Update AUCTIONS with winner_id
            cursor.execute('''
                UPDATE AUCTIONS SET winner_id = ?
                WHERE auction_id = ?
            ''', (winner_id, auction_id))

    conn.commit()
    conn.close()

assign_winners()

@app.route('/pay/<int:auction_id>', methods=['POST'])
def pay_for_won_item(auction_id):
    user_id = session.get('user_id')
    if not user_id:
        return "You must be logged in to pay", 403

    conn = sqlite3.connect('auction_platform.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get winner_id and winning_bid for this auction, confirm it's the current user
    cursor.execute('''
        SELECT AW.winner_id, AW.winning_bid
        FROM AUCTIONS A
        JOIN AUCTION_WINNERS AW ON A.winner_id = AW.winner_id
        WHERE A.auction_id = ? AND AW.user_id = ?
    ''', (auction_id, user_id))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Unauthorized or invalid auction", 403

    winner_id = row['winner_id']
    winning_bid = row['winning_bid']
    payment_date = datetime.now().isoformat()

    # 1. Insert payment
    cursor.execute('''
        INSERT INTO PAYMENT (amount, payment_date, payment_status)
        VALUES (?, ?, ?)
    ''', (winning_bid, payment_date, 'Completed'))
    payment_id = cursor.lastrowid

    # 2. Update AUCTION_WINNERS with payment_id
    cursor.execute('''
        UPDATE AUCTION_WINNERS
        SET payment_id = ?
        WHERE winner_id = ?
    ''', (payment_id, winner_id))

    conn.commit()
    conn.close()

    return redirect(url_for('profile'))
@app.route('/item_photos', methods=['GET'])
def get_itemphotos():
    itemphotos = query_db('SELECT * FROM ITEM_PHOTOS')
    return jsonify(itemphotos)
@app.route('/shipping', methods=['GET'])
def get_shipping():
    shipping = query_db('SELECT * FROM SHIPPING_DETAILS')
    return jsonify(shipping)
@app.route('/reviews', methods=['GET'])
def get_reviews():
    reviews = query_db('SELECT * FROM REVIEWS')
    return jsonify(reviews)
@app.route('/auction_winners', methods=['GET'])
def get_auction_winners():
    auction_winners = query_db('SELECT * FROM AUCTION_WINNERS')
    return jsonify(auction_winners)
@app.route('/categories/<int:category_id>/auctions', methods=['GET'])
def get_auctions_by_category(category_id):
    query = """
        SELECT 
            a.auction_id, a.start_date, a.end_date, a.starting_price, a.status,
            i.item_id, i.name AS item_name, i.description, i.photo_url
        FROM AUCTIONS a
        JOIN ITEMS i ON a.item_id = i.item_id
        WHERE i.category_id = ?
    """
    auctions = query_db(query, (category_id,))
    return jsonify(auctions)



@app.route('/users/<int:user_id>/payments', methods=['GET'])
def get_user_payments(user_id):
    payments = query_db("SELECT * FROM PAYMENT WHERE user_id = ?", (user_id,))
    return jsonify(payments)

@app.route('/payments/<int:payment_id>/pay', methods=['POST'])
def pay(payment_id):
    with sqlite3.connect('auction_platform.db') as conn:
        conn.execute("UPDATE PAYMENT SET status = 'Paid' WHERE payment_id = ?", (payment_id,))
    return jsonify({"message": "Payment marked as Paid"})
@app.route('/help')
def help():
    return render_template('help.html')
    
if __name__ == "__main__":
    app.run(debug=True)