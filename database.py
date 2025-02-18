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

def execute_multiple_queries(queries):
    """
    Execute multiple queries as an atomic transaction.
    queries: List of tuples (query, params)
    Returns True if successful, False if rollback occurs.
    """
    db = get_db_connection()
    try:
        cursor = db.cursor()
        for query, params in queries:
            cursor.execute(query, params)
        db.commit()  # Commit all queries together
        return True
    except sqlite3.Error as e:
        db.rollback()  # Roll back all queries if any fail
        print(f"Transaction failed: {e}")
        return False
    finally:
        cursor.close()

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

        CREATE TABLE IF NOT EXISTS market_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            time_transacted DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            stock_ticker TEXT NOT NULL,
            shares NUMERIC NOT NULL,
            price_per_share REAL NOT NULL,
            type TEXT NOT NULL,
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
                         
        CREATE TABLE IF NOT EXISTS p2p_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            time_transacted DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            stock_ticker TEXT NOT NULL,
            shares NUMERIC NOT NULL,
            price_per_share REAL NOT NULL,            
            comment TEXT,
            FOREIGN KEY (buyer_id) REFERENCES users(id),
            FOREIGN KEY (seller_id) REFERENCES users(id)
        );

        -- Users table: Ensure quick lookup by username and ID
        CREATE UNIQUE INDEX IF NOT EXISTS idx_username ON users (username);
        CREATE INDEX IF NOT EXISTS idx_user_id ON users (id);

        -- Stock Ownership: Fast lookup for a user's stock holdings
        CREATE INDEX IF NOT EXISTS idx_stock_ownership_user ON stock_ownership (user_id);
        CREATE INDEX IF NOT EXISTS idx_stock_ownership_ticker ON stock_ownership (stock_ticker);

        -- Market Transactions: Indexes for searching transactions by user and stock
        CREATE INDEX IF NOT EXISTS idx_market_transactions_user ON market_transactions (user_id);
        CREATE INDEX IF NOT EXISTS idx_market_transactions_ticker ON market_transactions (stock_ticker);
        CREATE INDEX IF NOT EXISTS idx_market_transactions_time ON market_transactions (time_transacted);

        -- P2P Market: Searching by user, stock ticker, and time
        CREATE INDEX IF NOT EXISTS idx_p2p_market_user ON p2p_market (user_id);
        CREATE INDEX IF NOT EXISTS idx_p2p_market_ticker ON p2p_market (stock_ticker);
        CREATE INDEX IF NOT EXISTS idx_p2p_market_time ON p2p_market (time_posted);

        -- P2P Transactions: Indexing buyer and seller for fast retrieval
        CREATE INDEX IF NOT EXISTS idx_p2p_transactions_buyer ON p2p_transactions (buyer_id);
        CREATE INDEX IF NOT EXISTS idx_p2p_transactions_seller ON p2p_transactions (seller_id);
        CREATE INDEX IF NOT EXISTS idx_p2p_transactions_ticker ON p2p_transactions (stock_ticker);
        CREATE INDEX IF NOT EXISTS idx_p2p_transactions_time ON p2p_transactions (time_transacted);
                         
        """)

        conn.commit()
         