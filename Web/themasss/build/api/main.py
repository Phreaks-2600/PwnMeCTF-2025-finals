import os

from flask import Flask, render_template_string, request
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "SQLALCHEMY_DATABASE_URI", "sqlite:////shared/sqlite/shared_db.sqlite"
)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    power = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)


@app.route("/upload", methods=["GET", "POST"])
@jwt_required()
def upload():
    identity = get_jwt_identity()
    if not identity.get("power", True):
        return render_template_string("Permission denied"), 403

    if request.method == "POST":
        f = request.files.get("file")
        if not f:
            return render_template_string("Error: No file provided."), 400

        filename = f.filename

        if " " in filename:
            return (
                render_template_string("Invalid filename: spaces are not allowed."),
                400,
            )

        upload_dir = "/shared/uploads/"
        f.save(os.path.join(upload_dir, f.filename))
        return render_template_string(f"{f.filename} uploaded successfully")

    return render_template_string("Unexpected error occurred"), 400


@app.after_request
def add_header(response):
    response.headers["Server"] = "Raspberry Pi 3 Model B+ V1.2"
    return response


if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)
