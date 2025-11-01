💰 CS50 Finance

CS50 Finance is a Flask web app that lets users manage a virtual stock portfolio.  
Users can register, log in, view real-time stock prices, buy and sell shares, and track their transaction history.  
Built with **Python**, **Flask**, and **SQLite**, it demonstrates authentication, APIs, and database integration.

---

🚀 Features
- 🔐 User registration and login with password hashing  
- 💵 Buy and sell stocks using live prices via an API  
- 📊 Portfolio overview with total holdings and cash balance  
- 🧾 Transaction history for all trades  
- ⚙️ Input validation and error handling  

---

🛠️ Technologies Used
- Python / Flask  
- SQLite  
- HTML / CSS / Jinja2  
- Flask-Session  
- IEX Cloud API (for stock data)

---

⚙️ How to Run Locally

1. Clone the repo
   git clone https://github.com/MohamedWalidElnabawy/Finance.git
   cd Finance


2. Create and activate a virtual environment

   python -m venv venv
   
   source venv/bin/activate     # macOS/Linux
   
   venv\Scripts\activate        # Windows

3. Install dependencies

   pip install -r requirements.txt


4. Set environment variables

   export FLASK_APP=application.py
   export FLASK_ENV=development
   export API_KEY=your_api_key_here



5. Run the app

   flask run

   Open your browser and go to: [http://127.0.0.1:5000]

---

## 📚 Learning Objectives

* Build dynamic web applications with Flask
* Use SQL databases for persistent data
* Manage user sessions and authentication securely
* Integrate third-party APIs for live data

---

## 🧠 Credits

Developed as part of **Harvard’s CS50: Introduction to Computer Science** course (Problem Set 9).

---