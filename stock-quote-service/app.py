from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

@app.route("/quote", methods=["GET"])
def get_stock_quote():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "Stock symbol is required"}), 400

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if "Global Quote" in data:
        stock_data = {
            "symbol": data["Global Quote"]["01. symbol"],
            "price": data["Global Quote"]["05. price"]
        }
        return jsonify(stock_data)
    else:
        return jsonify({"error": "Stock not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
