import plotly.graph_objects as go
import yfinance as yf
from flask import redirect, render_template, session
from functools import wraps

# Apology/error message
def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


# Login required
def login_required(f):
    """Decorate routes to require login."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Stock quote lookup
def lookup(symbol):
    """Look up stock quote for a given symbol using Yahoo Finance."""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        return {
            "name": info.get("longName", "Unknown"),
            "price": info.get("currentPrice"),
            "symbol": symbol.upper()
        }
    except Exception as e:
        print(f"Yahoo Finance API error: {e}")
        return None


# Format USD
def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

# Make stock chart using Plotly and Yahoo Finance
def get_stock_chart(symbol):
    stock = yf.Ticker(symbol)
    hist = stock.history(period="3mo")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close Price'))

    fig.update_layout(
        title=f"{symbol} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark"
    )

    return fig.to_html(full_html=False)
