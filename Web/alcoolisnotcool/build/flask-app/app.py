import socket
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

stock = {"beer": 10, "wine": 5, "ricard": 0}
prices = {"beer": 5, "wine": 8, "ricard": 51}
comments = []
user_balance = 50
DISCOUNT_CODE = "T0p_S3cr3t_D1sc0unt_C0d3_50%"


class Comment:
    def __init__(self, url):
        self.url = url
        response = requests.post(
            "http://localhost:5000/comment", json={"url": url}, timeout=5
        )
        self.index = len(comments) + 1
        self.comment = "Commentaire {self.index} :" + response.text
        comments.append(self.comment.format(self=self))


@app.route("/")
def index():
    return render_template(
        "index.html", stock=stock, user_balance=user_balance, prices=prices
    )


@app.route("/reset")
def reset():
    global stock, comments, user_balance
    stock = {"beer": 10, "wine": 5, "ricard": 0}
    comments = []
    user_balance = 50
    return redirect(url_for("index"))


@app.route("/comment", methods=["GET", "POST"])
def comment():
    if request.method == "POST":
        url = request.form.get("url", "")
        parsed = urlparse(url)
        print(url)
        scheme = parsed.scheme
        hostname = parsed.hostname
        port = parsed.port
        print(scheme, hostname, port)

        if "@" in url:
            return "This is not an email bro !!!", 400
        if "\\" in url:
            return "mmmh NO", 400
        if port:
            return "No custom port allowed", 400
        if scheme not in ["http", "https"]:
            return "Invalid scheme http or https only", 400

        if port is None:
            try:
                port = socket.getservbyname(scheme)
            except:
                return "Invalid scheme", 400

        if port == 443 and hostname != "pastebin.com" or port == 80:
            return "Invalid target domain only https on pastebin.com is allowed", 400

        try:
            Comment(url)
            return redirect(url_for("view_comments"))

        except requests.exceptions.RequestException:
            return "Error contacting helper", 500

    return render_template("comment.html")


@app.route("/comments")
def view_comments():
    return render_template("comments.html", comments=comments)


@app.route("/server_function/restock/<drink>", methods=["GET"])
def restock(drink):
    if request.remote_addr != "127.0.0.1":
        return "Access denied. This endpoint is only accessible from localhost.", 403

    if drink not in stock:
        return (
            f"Invalid drink! Available drinks are: {', '.join(stock.keys())}.",
            400,
        )

    stock[drink] += 10
    return f"Restocked! New stock: {stock[drink]}", 200


@app.route("/buy", methods=["POST"])
def buy():
    global user_balance
    data = request.get_json()
    drink = data.get("drink", "")
    discount_code = data.get("discount_code", "")

    if drink not in stock:
        return (
            jsonify(
                {
                    "message": f"Invalid drink! Available drinks are: {', '.join(stock.keys())}."
                }
            ),
            400,
        )

    if stock[drink] <= 0:
        return jsonify({"message": f"Sorry, {drink} is out of stock!"}), 400

    price = prices.get(drink, 0)
    discount_applied = False

    if discount_code == DISCOUNT_CODE:
        price = price / 2
        discount_applied = True

    if user_balance < price:
        return (
            jsonify(
                {"message": f"Not enough money to buy {drink}. You need {price} euros."}
            ),
            400,
        )

    user_balance -= price
    stock[drink] -= 1

    response_data = {
        "message": f"Enjoy your {drink}!",
        "stock": stock,
        "balance": user_balance,
        "prices": prices,
        "discount_applied": discount_applied,
    }

    if drink == "ricard":
        with open("./flag.txt", "r", encoding="utf-8") as f:
            flag = f.read().strip()
            response_data["message"] = f"Enjoy your Ricard! Here is the flag: {flag}"

    return jsonify(response_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1337, debug=True)
