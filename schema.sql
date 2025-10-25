
-- users, water_logs, tablets, glucose
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT,
    age INTEGER,
    gender TEXT,
    height REAL,
    weight REAL,
    goal TEXT,
    photo TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS water_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount_ml INTEGER,
    ts TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS tablets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    dosage TEXT,
    time TEXT,
    added_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS glucose (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    value REAL,
    ts TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS blood_pressure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    systolic REAL NOT NULL,
    diastolic REAL NOT NULL,
    ts TEXT NOT NULL
);
