import sqlite3
import random
import json
from datetime import datetime, timedelta

# Connect to the database (it will create the file if it doesn't exist)
conn = sqlite3.connect("auction_platform.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

# ========== TABLE CREATION ==========
# USERS Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS USERS (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT
);
''')

# CATEGORIES Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS CATEGORIES (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
''')

# ITEM_PHOTOS Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS ITEM_PHOTOS (
    photo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_url TEXT NOT NULL
);
''')

# ITEMS Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS ITEMS (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    condition TEXT,
    category_id INTEGER,
    photo_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES CATEGORIES(category_id),
    FOREIGN KEY (photo_id) REFERENCES ITEM_PHOTOS(photo_id)
);
''')

# PAYMENT Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS PAYMENT (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    payment_date TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);
''')

# SHIPPING_DETAILS Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS SHIPPING_DETAILS (
    shipping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT,
    shipping_status TEXT
);
''')

# REVIEWS Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS REVIEWS (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rating INTEGER,
    comment TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);
''')

# AUCTION_WINNERS Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS AUCTION_WINNERS (
    winner_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    shipping_id INTEGER,
    payment_id INTEGER,
    winning_bid REAL,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id),
    FOREIGN KEY (shipping_id) REFERENCES SHIPPING_DETAILS(shipping_id),
    FOREIGN KEY (payment_id) REFERENCES PAYMENT(payment_id)
);
''')

# AUCTIONS Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS AUCTIONS (
    auction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    winner_id INTEGER,
    review_id INTEGER,
    start_date TEXT,
    end_date TEXT,
    starting_price REAL,
    status TEXT,
    FOREIGN KEY (item_id) REFERENCES ITEMS(item_id),
    FOREIGN KEY (winner_id) REFERENCES AUCTION_WINNERS(winner_id),
    FOREIGN KEY (review_id) REFERENCES REVIEWS(review_id)
);
''')

# BIDS Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS BIDS (
    bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    auction_id INTEGER,
    bid_amount REAL,
    bid_time TEXT,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id),
    FOREIGN KEY (auction_id) REFERENCES AUCTIONS(auction_id)
);
''')

# ========== SAMPLE DATA INSERTION ==========
categories = [
    {"name": "Art"},
    {"name": "Electronics"},
    {"name": "Jewellery"},
    {"name": "Fashion"},
    {"name": "Cars and Bikes"},
    {"name": "Interiors"}
]

image_urls = [
    "https://cdn.pixabay.com/photo/2017/01/07/17/48/interior-1961070_1280.jpg",
    "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg",
    "https://cdn.pixabay.com/photo/2016/11/29/09/32/adult-1868750_1280.jpg",
    "https://cdn.pixabay.com/photo/2015/12/01/20/28/road-1072823_1280.jpg"
]

# Populate CATEGORIES Table
for category in categories:
    cursor.execute("INSERT INTO CATEGORIES (name) VALUES (?)", (category["name"],))

# Populate ITEM_PHOTOS Table (using random image URLs)
for i in range(1, 61):
    cursor.execute("INSERT INTO ITEM_PHOTOS (photo_url) VALUES (?)", (random.choice(image_urls),))

# Populate USERS Table
for i in range(1, 61):
    cursor.execute("INSERT INTO USERS (name, email, password, role) VALUES (?, ?, ?, ?)",
                   (f"User{i}", f"user{i}@example.com", "pass123", "seller" if i % 2 == 1 else "buyer"))

# Populate ITEMS Table
for i in range(1, 61):
    category_id = random.randint(1, 6)  # Randomly assign category
    photo_id = random.randint(1, 60)  # Randomly assign photo
    cursor.execute("""
        INSERT INTO ITEMS (name, description, condition, category_id, photo_id)
        VALUES (?, ?, ?, ?, ?)""",
        (f"Item{i}", f"Description for Item{i}", "new" if i % 2 == 0 else "used", category_id, photo_id))

# Populate PAYMENT Table
for i in range(1, 61):
    amount = round(random.uniform(100, 1000), 2)
    date = (datetime.now() - timedelta(days=random.randint(1, 100))).strftime('%Y-%m-%d')
    cursor.execute("INSERT INTO PAYMENT (amount, payment_date, user_id) VALUES (?, ?, ?)",
                   (amount, date, random.randint(1, 60)))

# Populate SHIPPING_DETAILS Table
for i in range(1, 61):
    status = random.choice(["pending", "shipped", "delivered"])
    cursor.execute("INSERT INTO SHIPPING_DETAILS (address, shipping_status) VALUES (?, ?)",
                   (f"123 Lane {i}, City", status))

# Populate REVIEWS Table
for i in range(1, 61):
    rating = random.randint(1, 5)
    cursor.execute("INSERT INTO REVIEWS (rating, comment, user_id) VALUES (?, ?, ?)",
                   (rating, f"This is review {i}", random.randint(1, 60)))

# Populate AUCTION_WINNERS Table
for i in range(1, 61):
    bid = round(random.uniform(150, 2000), 2)
    cursor.execute("""
        INSERT INTO AUCTION_WINNERS (user_id, shipping_id, payment_id, winning_bid)
        VALUES (?, ?, ?, ?)""",
        (random.randint(1, 60), i, i, bid))

# Populate AUCTIONS Table
for i in range(1, 61):
    item_id = random.randint(1, 60)
    winner_id = random.randint(1, 60)
    review_id = random.randint(1, 60)
    start_date = (datetime.now() - timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d')
    end_date = (datetime.now() - timedelta(days=random.randint(1, 29))).strftime('%Y-%m-%d')
    starting_price = round(random.uniform(50, 500), 2)
    status = random.choice(["active", "completed"])
    cursor.execute("""
        INSERT INTO AUCTIONS (item_id, winner_id, review_id, start_date, end_date, starting_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (item_id, winner_id, review_id, start_date, end_date, starting_price, status))

# Populate BIDS Table
for i in range(1, 101):
    user_id = random.randint(1, 60)
    auction_id = random.randint(1, 60)
    bid_amount = round(random.uniform(60, 2500), 2)
    bid_time = (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO BIDS (user_id, auction_id, bid_amount, bid_time) VALUES (?, ?, ?, ?)",
                   (user_id, auction_id, bid_amount, bid_time))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("✅ Tables created and populated with 60+ entries each (except BIDS with 100)")
