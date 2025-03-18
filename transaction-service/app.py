from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests
import os
from dotenv import load_dotenv

# Memuat variabel lingkungan dari .env
load_dotenv()

# Ambil DATABASE_URL dari .env
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/transaction_db")

# Ambil API Key dari .env
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
print("Using API Key:", ALPHA_VANTAGE_API_KEY)  # Debugging

app = Flask(__name__)

# Konfigurasi Database
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Inisialisasi Flask-Migrate

# Model database untuk transaksi saham
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    stock_symbol = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # "buy" atau "sell"

# Endpoint untuk halaman utama
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Transaction Service is running!"}), 200

# Fungsi untuk mendapatkan harga saham dari Alpha Vantage API
def get_stock_price(symbol):
    if not ALPHA_VANTAGE_API_KEY:
        return None  # Jika API Key tidak ditemukan
    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        try:
            return float(data["Global Quote"]["05. price"])  # Mengambil harga saham terbaru
        except KeyError:
            return None  # Jika data tidak ditemukan
    else:
        return None

# Endpoint untuk melakukan transaksi beli saham
@app.route("/buy", methods=["POST"])
def buy_stock():
    data = request.json
    user_id = data.get("user_id")
    symbol = data.get("symbol")
    shares = data.get("shares")

    if not user_id or not symbol or not shares:
        return jsonify({"error": "user_id, symbol, and shares are required"}), 400

    price = get_stock_price(symbol)  # Ambil harga saham dari API
    if price is None:
        return jsonify({"error": "Failed to fetch stock price"}), 500

    new_transaction = Transaction(
        user_id=user_id,
        stock_symbol=symbol.upper(),
        shares=int(shares),
        price=price,
        type="buy"
    )
    db.session.add(new_transaction)
    db.session.commit()

    return jsonify({"message": "Stock purchase successful", "transaction_id": new_transaction.id}), 201

# Endpoint untuk melakukan transaksi jual saham
@app.route("/sell", methods=["POST"])
def sell_stock():
    data = request.json
    user_id = data.get("user_id")
    symbol = data.get("symbol")
    shares = data.get("shares")

    if not user_id or not symbol or not shares:
        return jsonify({"error": "user_id, symbol, and shares are required"}), 400

    price = get_stock_price(symbol)  # Ambil harga saham dari API
    if price is None:
        return jsonify({"error": "Failed to fetch stock price"}), 500

    new_transaction = Transaction(
        user_id=user_id,
        stock_symbol=symbol.upper(),
        shares=int(shares),
        price=price,
        type="sell"
    )
    db.session.add(new_transaction)
    db.session.commit()

    return jsonify({"message": "Stock sale successful", "transaction_id": new_transaction.id}), 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Membuat tabel transaksi di database jika belum ada
    app.run(host="0.0.0.0", port=5002)
