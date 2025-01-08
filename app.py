from flask import Flask, request, render_template, jsonify
from threading import Thread
import time
import requests
import re

app = Flask(__name__)

# Global variables
BITCOIN_PRICE = 0
GUESSES = []
ALLOW_SUBMISSIONS = True  # Global variable to enable/disable submissions
fetching_enabled = True  # Flag to control price fetching

def calculate_difference(guess):
    return abs(guess['guess'] - BITCOIN_PRICE)

# Fetch Bitcoin price periodically
def fetch_bitcoin_price():
    global BITCOIN_PRICE, GUESSES
    global fetching_enabled
    while True:
        if fetching_enabled:  # Only fetch price if fetching is enabled
            try:
                response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=sgd")
                if response.status_code == 200:
                    BITCOIN_PRICE = response.json().get("bitcoin", {}).get("sgd", 0)
                    print(f"Fetched Bitcoin Price: {BITCOIN_PRICE}")

                    # Update differences and rankings for each guess
                    for guess in GUESSES:
                        guess['difference'] = calculate_difference(guess)

                    # Sort guesses based on the closest to the Bitcoin price
                    sorted_guesses = sorted(GUESSES, key=lambda x: x['difference'])

                    # Store updated guesses for leaderboard
                    GUESSES = sorted_guesses
            except Exception as e:
                print(f"Error fetching Bitcoin price: {e}")
        time.sleep(30)  # Wait for the next fetch

def pause_fetching():
    global fetching_enabled
    fetching_enabled = False
    print("Bitcoin price fetching paused.")

def resume_fetching():
    global fetching_enabled
    fetching_enabled = True
    print("Bitcoin price fetching resumed.")

@app.route("/pause_bitcoin_fetch", methods=["POST"])
def pause_bitcoin_fetch():
    pause_fetching()  # Pause the fetching
    return jsonify({"message": "Bitcoin price fetching paused!"})

@app.route("/resume_bitcoin_fetch", methods=["POST"])
def resume_bitcoin_fetch():
    resume_fetching()  # Resume the fetching
    return jsonify({"message": "Bitcoin price fetching resumed!"})

@app.route("/")
def home():
    # Pass all guesses sorted by their difference
    sorted_guesses = sorted(GUESSES, key=lambda x: x["difference"])
    return render_template("index.html", bitcoin_price=BITCOIN_PRICE, leaderboard=sorted_guesses)

@app.route("/get_submission_status", methods=["GET"])
def get_submission_status():
    return jsonify({"status": ALLOW_SUBMISSIONS})


@app.route("/start_submissions", methods=["POST"])
def start_submissions():
    global ALLOW_SUBMISSIONS
    ALLOW_SUBMISSIONS = True
    return jsonify({"message": "Submissions have been enabled."})

@app.route("/pause_submissions", methods=["POST"])
def pause_submissions():
    global ALLOW_SUBMISSIONS
    ALLOW_SUBMISSIONS = False
    return jsonify({"message": "Submissions have been disabled."})

@app.route("/submit_guess", methods=["POST"])
def submit_guess():
    if not ALLOW_SUBMISSIONS:
        return jsonify({"message": "Submissions are currently disabled."}), 403

    data = request.get_json()  # Parse JSON payload
    email = data.get("email").strip()
    guess = data.get("guess")

    if not re.match(r"^[a-zA-Z0-9._]+$", email):
        return jsonify({"message": "Invalid email format!"}), 400

    if email and guess is not None:
        guess = float(guess)

        for entry in GUESSES:
            if entry["email"] == email:
                entry["guess"] = guess
                entry["difference"] = abs(guess - BITCOIN_PRICE)
                break
        else:
            GUESSES.append({"email": email, "guess": guess, "difference": abs(guess - BITCOIN_PRICE)})

        return jsonify({"message": "Guess submitted successfully!"})
    else:
        return jsonify({"message": "Invalid input!"}), 400


@app.route("/leaderboard")
def leaderboard():
    sorted_guesses = sorted(GUESSES, key=lambda x: x["difference"])
    return jsonify(sorted_guesses)

@app.route("/get_leaderboard_count", methods=["GET"])
def get_leaderboard_count():
    return jsonify({"count": len(GUESSES)})

@app.route("/remove_guess", methods=["POST"])
def remove_guess():
    email_to_remove = request.form.get("email")
    
    # Find and remove the guess for the given email
    global GUESSES
    GUESSES = [guess for guess in GUESSES if guess.get("email") != email_to_remove]
    
    return jsonify({"message": f"Guess for {email_to_remove} removed!"})


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
