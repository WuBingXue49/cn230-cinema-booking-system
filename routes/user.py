from flask import Blueprint, jsonify, request
from db import get_db_connection
import mysql.connector
from auth import require_role_decorator, get_current_user

user_bp = Blueprint("user", __name__)


@user_bp.route("/me", methods=["GET"])
@require_role_decorator(["customer", "staff", "admin"])
def get_me():
    current_user_id, _ = get_current_user()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT user_id, name, email, role FROM Users WHERE user_id = %s",
        (current_user_id,),
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return jsonify({"status": "success", "data": user})
    return jsonify({"status": "error", "message": "User not found"}), 404


@user_bp.route("/<int:user_id>", methods=["GET"])
@require_role_decorator(["customer", "staff", "admin"])
def get_user(user_id):
    """
    Get user info by user_id
    e.g. http://127.0.0.1:5000/users/1 or other user_ids
    """
    current_user_id, role = get_current_user()
    if int(current_user_id) != user_id and role not in ["staff", "admin"]:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT user_id, name, email, role FROM Users WHERE user_id = %s", (user_id,)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return jsonify({"status": "success", "data": user})
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404


@user_bp.route("/", methods=["GET"])
@require_role_decorator(["staff", "admin"])
def get_users():
    """
    Get all users
    -> http://127.0.0.1:5000/users/
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT user_id, name, email, role FROM Users")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"status": "success", "data": users})


@user_bp.route("/staff/bookings", methods=["GET"])
@require_role_decorator(["staff", "admin"])
def staff_list_bookings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.booking_id,
               u.user_id,
               u.name AS user_name,
               m.title,
               t.theater_name,
               st.show_date,
               b.status
        FROM Booking b
        JOIN Users u ON b.user_id = u.user_id
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        JOIN Theater t ON st.theater_id = t.theater_id
        ORDER BY st.show_date DESC
    """)
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": bookings})


@user_bp.route("/staff/bookings/<int:booking_id>/checkin", methods=["PUT"])
@require_role_decorator(["staff", "admin"])
def staff_checkin_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT booking_id, status FROM Booking WHERE booking_id = %s",
            (booking_id,),
        )
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking["status"] == "Cancelled":
            return jsonify(
                {"status": "error", "message": "Cannot check in a cancelled booking"}
            ), 400
        if booking["status"] == "Used":
            return jsonify(
                {"status": "error", "message": "Booking already checked in"}
            ), 400
        if booking["status"] != "Confirmed":
            return jsonify(
                {
                    "status": "error",
                    "message": "Booking must be confirmed (paid) before check-in",
                }
            ), 400

        cursor.execute(
            "UPDATE Booking SET status = 'Used' WHERE booking_id = %s", (booking_id,)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Booking checked in"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@user_bp.route("/<int:user_id>/bookings", methods=["GET"])
@require_role_decorator(["staff", "admin"])
def get_user_bookings(user_id):
    """
    Get booking history for user
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT b.booking_id, m.title, t.theater_name, st.show_date, st.price
        FROM Booking b
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        JOIN Theater t ON st.theater_id = t.theater_id
        WHERE b.user_id = %s
    """,
        (user_id,),
    )
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": bookings})


@user_bp.route("/no-booking", methods=["GET"])
@require_role_decorator(["staff", "admin"])
def get_users_no_booking():
    """
    Get customers with no bookings
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.name
        FROM Users u
        LEFT JOIN Booking b ON u.user_id = b.user_id
        WHERE b.booking_id IS NULL
        AND u.role = 'customer'
    """)
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": users})


@user_bp.route("/", methods=["POST"])
@require_role_decorator("admin")
def create_user():
    """
    Create a new user
    """
    data = request.get_json()
    user_id = data.get("user_id")
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    if not all([user_id, name, email, password, role]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Users (user_id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
            (user_id, name, email, password, role),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "User created"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@user_bp.route("/register", methods=["POST"])
def register_user():
    """
    Public registration for new customer users.
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "customer")
    if not all([user_id, name, email, password]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    if role != "customer":
        return jsonify(
            {
                "status": "error",
                "message": "Public registration only allows role=customer",
            }
        ), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Users (user_id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
            (user_id, name, email, password, role),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "User registered successfully"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
