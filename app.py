import os
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from db import get_db_connection
from routes.booking import booking_bp
from routes.showtime import showtime_bp
from routes.user import user_bp
from routes.movies import movies_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.register_blueprint(booking_bp, url_prefix="/bookings")
app.register_blueprint(showtime_bp, url_prefix="/showtimes")
app.register_blueprint(user_bp, url_prefix="/users")
app.register_blueprint(movies_bp, url_prefix="/movies")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify(
            {"status": "error", "message": "Email and password required"}
        ), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT user_id, name, role, password FROM Users WHERE email = %s", (email,)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or user["password"] != password:
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401

    session.clear()
    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    session["role"] = user["role"]

    return jsonify(
        {
            "status": "success",
            "data": {
                "user_id": user["user_id"],
                "name": user["name"],
                "role": user["role"],
            },
        }
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"})


@app.route("/auth/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    return jsonify(
        {
            "status": "success",
            "data": {
                "user_id": session.get("user_id"),
                "name": session.get("name"),
                "role": session.get("role"),
            },
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
