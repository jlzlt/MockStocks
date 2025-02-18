# MockStocks

A stock trading simulation web application that allows users to **buy, sell, and track stocks** in their portfolio. The platform fetches real-time stock prices, updates user balances, and maintains a transaction history.

Additionally, it features a **peer-to-peer (P2P) market**, where registered users can trade stocks with each other. You can create multiple profiles to test P2P trade proposals.

This project was built as part of my Vinted Academy submission, showcasing my skills in Python, Flask, SQLite, and web development.


## Installation Guide

Follow these steps to set up and run MockStocks on your local machine:

### 1.) Prerequisites
Make sure you have the following installed:  

• Python 3.10+ (https://www.python.org/downloads/)  
• pip (comes with Python)  
• Git (https://git-scm.com/downloads)  
• Virtual Environment (venv) (optional but recommended)

### 2.) Clone the Repository
Open a terminal and run:  

`git clone https://github.com/jlzlt/MockStocks.git`  
`cd MockStocks`  


### 3.) Create a Virtual Environment (Optional, Recommended)
To keep dependencies isolated, create and activate a virtual environment:  

Windows:  
`python -m venv venv`  
`venv\Scripts\activate`  

Mac/Linux:  
`python3 -m venv venv`  
`source venv/bin/activate`  

### 4.) Install Dependencies
Run the following command to install required packages:  
`pip install -r requirements.txt`  

### 5.) Run the Application
Start the application by running:  
`python app.py`  

The app will be available at: http://127.0.0.1:5000/


## Features

### Security & Authentication

- Secure user registration, login, and logout system  
- Password hashing for secure storage  
- Session management:  
  - Timeout after 15 minutes of inactivity  
  - Uses server-side storage (filesystem) instead of signed cookies  
  - Prevents JavaScript from accessing the session cookie  
  - CSRF protection (Cross-Site Request Forgery prevention)  

### Stock Trading System

- Real-time stock prices fetched from Yahoo Finance API  
- Buy/sell stocks at current market prices  
- Transaction history tracking all trades  
- Portfolio management displaying owned stocks and balance  

### Peer-to-Peer (P2P) Market

- Registered users can trade stocks with each other  
- Funds and stocks are frozen while a trade proposal is active  
- Users can edit or remove trade proposals  

### Security Enhancements

- Rate limiting to prevent malicious requests  
- Race condition handling with atomic database transactions  

### Visualization & Analytics

- Stock data visualization using Plotly and yfinance  


## Tech Stack

- Backend: Python, Flask, SQLite3  
- Frontend: HTML, CSS, JavaScript  
- APIs: Yahoo Finance API  
- Libraries: Plotly, yfinance  
 