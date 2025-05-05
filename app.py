from flask import Flask, request, jsonify
import requests
import json
from decimal import Decimal

app = Flask(__name__)

API_KEY = "6ed7b13e-063c-42fc-a27b-9bd87f8f7219"
BASE_URL = "https://api-mainnet.magiceden.dev/v2/ord/btc/runes"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

@app.route("/")
def index():
    return "BTC Rune Tracker API is running."

@app.route("/analyze", methods=["GET"])
def analyze():
    address = request.args.get("address", "").strip()
    rune_input = request.args.get("rune", "").strip().upper().replace(" ", "")

    if not address or not rune_input:
        return jsonify({"error": "Missing 'address' or 'rune' query parameter"}), 400

    offset = 0
    limit = 100
    all_data = []

    try:
        while True:
            res = requests.get(
                f"{BASE_URL}/wallet/activities/{address}",
                headers=HEADERS,
                params={"offset": offset, "limit": limit}
            )
            data = res.json()
            if not data:
                break
            all_data.extend(data)
            if len(data) < limit:
                break
            offset += limit
    except Exception as e:
        return jsonify({"error": f"API fetch failed: {str(e)}"}), 500

    total_units_received = 0
    total_units_sold = 0
    total_satoshis_spent = 0
    total_satoshis_earned = 0

    for tx in all_data:
        rune = tx.get("rune", "").upper().replace(" ", "")
        if rune != rune_input:
            continue

        kind = tx.get("kind", "")
        amount = int(tx.get("amount", 0))
        sats = tx.get("txValueSatoshi") or tx.get("listedPrice") or 0
        from_addr = tx.get("oldOwner")
        to_addr = tx.get("newOwner")

        if kind == "received":
            total_units_received += amount
        elif kind == "buying_broadcasted" and to_addr == address:
            total_satoshis_spent += sats
        elif kind == "sent":
            total_units_sold += amount
            total_satoshis_earned += sats

    return jsonify({
        "rune": rune_input,
        "units_received": float(Decimal(total_units_received) / Decimal(1e5)),
        "units_sold": float(Decimal(total_units_sold) / Decimal(1e5)),
        "btc_spent": float(Decimal(total_satoshis_spent) / Decimal(1e8)),
        "btc_earned": float(Decimal(total_satoshis_earned) / Decimal(1e8))
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)