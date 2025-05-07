from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import random,sqlite3




app = Flask(__name__)
DB_FILE = 'auction_platform.db'
otp_storage = {}

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



# Corrected data with colons (:) instead of equals signs (=)

# ✅ Signup Route with OTP and password confirmation
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']
    confirm_password = data['confirm_password']

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match ❌"}), 400

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = {'otp': otp, 'data': (name, email, password)}
    return jsonify({"message": "OTP sent (simulated)", "otp": otp}), 200

# 🔐 Confirm Signup using OTP
@app.route('/signup/verify', methods=['POST'])
def verify_signup():
    data = request.get_json()
    email = data['email']
    otp = data['otp']

    stored = otp_storage.get(email)
    if not stored or stored['otp'] != otp:
        return jsonify({"error": "Invalid or expired OTP ❌"}), 400

    name, email, password = stored['data']
    try:
        conn = get_db()
        conn.execute("INSERT INTO USERS (name, email, password, role) VALUES (?, ?, ?, ?)",
                     (name, email, password, 'buyer'))
        conn.commit()
        del otp_storage[email]
        return jsonify({"message": "Signup complete ✅"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists ❌"}), 409

# 🔐 Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    conn = get_db()
    user = conn.execute("SELECT * FROM USERS WHERE email=? AND password=?", (email, password)).fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful ✅", "user": dict(user)}), 200
    return jsonify({"error": "Invalid credentials ❌"}), 401

# 🔐 Forgot password - request OTP
@app.route('/forgot', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data['email']

    conn = get_db()
    user = conn.execute("SELECT * FROM USERS WHERE email=?", (email,)).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Email not found ❌"}), 404

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = {'otp': otp}
    return jsonify({"message": "OTP sent (simulated)", "otp": otp}), 200

# 🔐 Reset password with OTP
@app.route('/reset', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data['email']
    otp = data['otp']
    new_password = data['new_password']
    confirm_password = data['confirm_password']

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match ❌"}), 400

    stored = otp_storage.get(email)
    if not stored or stored['otp'] != otp:
        return jsonify({"error": "Invalid or expired OTP ❌"}), 400

    conn = get_db()
    conn.execute("UPDATE USERS SET password=? WHERE email=?", (new_password, email))
    conn.commit()
    conn.close()

    del otp_storage[email]
    return jsonify({"message": "Password reset successfully ✅"}), 200
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
    users = conn.execute("SELECT user_id, name, email, role FROM USERS").fetchall()
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

# 📂 Get all categories
@app.route('/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM CATEGORIES")
    categories = cursor.fetchall()
    conn.close()

    return jsonify([dict(cat) for cat in categories]), 200
@app.route('/auctions', methods=['GET'])
def get_auctions():
    auctions = query_db('SELECT * FROM AUCTIONS')
    return jsonify(auctions)
@app.route('/bids', methods=['GET'])
def get_bids():
    bids = query_db('SELECT * FROM BIDS')
    return jsonify(bids)
@app.route('/payment', methods=['GET'])
def get_payment():
    payment = query_db('SELECT * FROM PAYMENT')
    return jsonify(payment)
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

if __name__ == "__main__":
    app.run(debug=True)
