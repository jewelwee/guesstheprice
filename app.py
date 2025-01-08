from flask import Flask, request, render_template, jsonify
from threading import Thread
import time
import requests

app = Flask(__name__)

# Global variables
BITCOIN_PRICE = 0
GUESSES = []

# Fetch Bitcoin price periodically
def fetch_bitcoin_price():
    global BITCOIN_PRICE
    while True:
        try:
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
            if response.status_code == 200:
                BITCOIN_PRICE = response.json().get("bitcoin", {}).get("usd", 0)
        except Exception as e:
            print(f"Error fetching Bitcoin price: {e}")
        time.sleep(60)  # 1-minute interval

@app.route("/")
def home():
    return render_template("index.html", bitcoin_price=BITCOIN_PRICE)

@app.route("/submit_guess", methods=["POST"])
def submit_guess():
    data = request.get_json()  # Parse JSON payload
    email = data.get("email")
    guess = data.get("guess")

    if email and guess is not None:
        guess = float(guess)
        # Add guess to the leaderboard
        GUESSES.append({"email": email, "guess": guess, "difference": abs(guess - BITCOIN_PRICE)})
        return jsonify({"message": "Guess submitted successfully!"})
    else:
        return jsonify({"message": "Invalid input!"}), 400

@app.route("/leaderboard")
def leaderboard():
    sorted_guesses = sorted(GUESSES, key=lambda x: x["difference"])
    return jsonify(sorted_guesses)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        admin_action = request.form.get("action")
        if admin_action == "clear_leaderboard":
            GUESSES.clear()
            return jsonify({"message": "Leaderboard cleared!"})
    return render_template("admin.html")

if __name__ == "__main__":
    # Start the price-fetching thread
    price_thread = Thread(target=fetch_bitcoin_price, daemon=True)
    price_thread.start()

    # Run Flask app
    app.run(debug=True)
