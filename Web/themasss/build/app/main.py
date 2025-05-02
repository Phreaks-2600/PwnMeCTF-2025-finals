import os
import uuid

from flask import Flask, jsonify, render_template, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "SQLALCHEMY_DATABASE_URI", "sqlite:////shared/sqlite/shared_db.sqlite"
)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    power = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)


class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", href="/login", text="login")


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    phone_number = data.get("phone_number")

    if not all([username, password, first_name, last_name, email, phone_number]):
        return jsonify({"message": "All fields are required"}), 400

    if (
        User.query.filter_by(username=username).first()
        or User.query.filter_by(email=email).first()
        or User.query.filter_by(phone_number=phone_number).first()
    ):
        return (
            jsonify({"message": "username, email, or phone number already exists"}),
            409,
        )

    if phone_number.isdigit() and len(phone_number) != 10:
        return jsonify({"message": "Valid phone number is required"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(
        username=username,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("index.html", href="/", text="home")

    elif request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        username = data.get("username")
        password = data.get("password")
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(
                identity={"id": user.id, "username": user.username,"power": user.power}
            )
            return (
                jsonify({"username": user.username, "access_token": access_token}),
                200,
            )

        return jsonify({"message": "Invalid credentials"}), 401


@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    identity = get_jwt_identity()
    user = User.query.filter_by(id=identity["id"]).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    user_data = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "power": user.power,
    }
    return jsonify(user_data), 200


@app.route("/update_password", methods=["PATCH"])
@jwt_required()
def update_password():
    identity = get_jwt_identity()
    user = User.query.filter_by(id=identity["id"]).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    if data is None:
        return jsonify({"message": "No JSON data provided"}), 400

    old_password = data.get("old_password")
    new_password = data.get("new_password")
    specified_username = data.get("username")

    if not all([specified_username, old_password, new_password]):
        return (
            jsonify(
                {
                    "message": "username, old_password and new_password fields are required"
                }
            ),
            400,
        )

    if specified_username != user.username:
        return jsonify({"message": "Invalid username"}), 404

    if not old_password and not new_password:
        return (
            jsonify({"message": "old_password and new_password fields are required."}),
            400,
        )

    if not bcrypt.check_password_hash(user.password, old_password):
        return jsonify({"message": "Invalid old_password"}), 401

    if old_password == new_password:
        return (
            jsonify({"message": "new_password cannot be the same as old_password"}),
            400,
        )

    for key, value in data.items():
        if hasattr(user, key) and key != "id":
            setattr(user, key, value)

    user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()

    jti = get_jwt()["jti"]
    revoked_token = TokenBlocklist(jti=jti)
    db.session.add(revoked_token)
    db.session.commit()

    return (
        jsonify({"message": "Password updated successfully! Please reauthenticate."}),
        200,
    )


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = TokenBlocklist.query.filter_by(jti=jti).first()
    return token is not None


@app.after_request
def add_header(response):
    response.headers["Server"] = "Raspberry Pi 3 Model B+ V1.2"
    return response


if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
