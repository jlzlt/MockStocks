import sqlite3
from flask import g

DATABASE = "mockstocks.db"

def get_db_connection():
    """Open a new database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Makes rows return as dictionaries
    return g.db

def close_db(exception=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def execute_query(query, params=(), fetchone=False):
    """Execute a query and return results as a list of dictionaries."""
    db = get_db_connection()
    try:
        cursor = db.execute(query, params)

        # Auto-commit for data-modifying queries
        if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            db.commit()

        # Always return a list, even if fetching one result
        if fetchone:
            result = cursor.fetchone()
            return [result] if result else []  # Wrap in a list if not None
        else:
            return cursor.fetchall()  # Already a list
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []  # Return an empty list on error
    finally:
        cursor.close()  # Always close the cursor

def initialize_database():
    """Ensure required tables exist in the database."""
    with sqlite3.connect(DATABASE) as conn:
        db = conn.cursor()

        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            hash TEXT NOT NULL,
            cash NUMERIC NOT NULL DEFAULT 10000.00,
            frozen_cash NUMERIC DEFAULT 0.00
        );
                         
        CREATE TABLE IF NOT EXISTS stock_ownership (
            ownership_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            stock_ticker TEXT NOT NULL,
            amount NUMERIC NOT NULL,
            frozen_amount NUMERIC DEFAULT 0.00,
            avg_price REAL NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE (user_id, stock_ticker)
        );

        CREATE TABLE IF NOT EXISTS stock_buys (
            buy_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            time_bought DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            stock_bought TEXT NOT NULL,
            price_bought REAL NOT NULL,
            amount_bought NUMERIC NOT NULL,
            type TEXT NOT NULL,
            p2p_counterpartyid INTEGER,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS stock_sells (
            sell_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            time_sold DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            stock_sold TEXT NOT NULL,
            price_sold REAL NOT NULL,
            amount_sold NUMERIC NOT NULL,
            type TEXT NOT NULL,
            p2p_counterpartyid INTEGER,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
                         
        CREATE TABLE IF NOT EXISTS p2p_market (
            p2p_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            time_posted DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            stock_ticker TEXT NOT NULL,
            amount NUMERIC NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL,
            comment TEXT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Indexes for faster lookups
        CREATE UNIQUE INDEX IF NOT EXISTS idx_username ON users (username);
        CREATE INDEX IF NOT EXISTS idx_user_id_buys ON stock_buys (user_id);
        CREATE INDEX IF NOT EXISTS idx_user_id_sells ON stock_sells (user_id);
        CREATE INDEX IF NOT EXISTS idx_stock_ownership_user_id ON stock_ownership (user_id);
        CREATE INDEX IF NOT EXISTS idx_p2p_market_user_id ON p2p_market (user_id);
        CREATE INDEX IF NOT EXISTS idx_stock_buys_ticker ON stock_buys (stock_bought);
        CREATE INDEX IF NOT EXISTS idx_stock_sells_ticker ON stock_sells (stock_sold);
        CREATE INDEX IF NOT EXISTS idx_p2p_market_ticker ON p2p_market (stock_ticker);
        CREATE INDEX IF NOT EXISTS idx_stock_buys_time ON stock_buys (time_bought);
        CREATE INDEX IF NOT EXISTS idx_stock_sells_time ON stock_sells (time_sold);
        CREATE INDEX IF NOT EXISTS idx_p2p_market_time ON p2p_market (time_posted);
        """)

        conn.commit()