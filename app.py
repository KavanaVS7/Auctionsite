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

# Corrected data with colons (:) instead of equals signs (=)
new_items_data = [
    {
        "item_id": 29,
        "name": "Outfit",
        "description": "Fitchexk",
        "photo_url": "https://cdn.pixabay.com/photo/2016/11/22/21/57/apparel-1850804_1280.jpg"
    },
    {
        "item_id": 30,
        "name": "Cupboard",
        "description": "ALl in one",
        "photo_url": "https://cdn.pixabay.com/photo/2017/09/09/18/25/living-room-2732939_1280.jpg"
    },
    {
        "item_id": 31,
        "name": "Mouse",
        "description": "he computer mouse is a handheld pointing device used to control a cursor on a computer screen, allowing users to interact with the computer",
        "photo_url": "https://cdn.pixabay.com/photo/2017/11/27/21/31/computer-2982270_1280.jpg"
    },
    {
        "item_id": 32,
        "name": "Vibewithvintage",
        "description": "A vintage car is generally an old automobile ",
        "photo_url": "'https://cdn.pixabay.com/photo/2015/12/15/09/20/car-1093927_1280.jpg,"
    },
    {
        "item_id": 33,
        "name": "Flower vase",
        "description": "Decorate it with flower",
        "photo_url": "https://cdn.pixabay.com/photo/2017/09/09/18/25/living-room-2732939_1280.jpg"
    },
    {
        "item_id": 34,
        "name": "Camera",
        "description": "Pause the moment",
        "photo_url": "https://cdn.pixabay.com/photo/2017/11/27/21/31/computer-2982270_1280.jpg"
    },
     
     
    # Add more items as needed
]

# Loop through and update the data
for item in new_items_data:
    cursor.execute("""
        UPDATE items
        SET name = ?, description = ?, photo_url = ?
        WHERE item_id = ?
    """, (item["name"], item["description"], item["photo_url"], item["item_id"]))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Data updated successfully.")



print("Items updated successfully.")


print("Items updated successfully.")
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
if __name__ == "__main__":
    app.run(debug=True)
