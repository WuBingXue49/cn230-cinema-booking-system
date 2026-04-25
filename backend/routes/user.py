from flask import Blueprint, jsonify, request
from db import get_db_connection
import mysql.connector
from auth import require_role_decorator

user_bp = Blueprint('user', __name__)

@user_bp.route('/<int:user_id>', methods=['GET'])
@require_role_decorator(['staff', 'admin'])
def get_user(user_id):
    """
    Get user info by user_id
    e.g. http://127.0.0.1:5000/users/1 or other user_ids
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return jsonify({"status": "success", "data": user})
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404

@user_bp.route('/', methods=['GET'])
@require_role_decorator(['staff', 'admin'])
def get_users():
    '''
    Get all users
    -> http://127.0.0.1:5000/users/
    '''
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"status": "success", "data": users})

@user_bp.route('/<int:user_id>/bookings', methods=['GET'])
@require_role_decorator(['staff', 'admin'])
def get_user_bookings(user_id):
    """
    Get booking history for user
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.booking_id, m.title, t.theater_name, st.show_date, st.price
        FROM Booking b
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        JOIN Theater t ON st.theater_id = t.theater_id
        WHERE b.user_id = %s
    """, (user_id,))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": bookings})

@user_bp.route('/no-booking', methods=['GET'])
@require_role_decorator(['staff', 'admin'])
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

@user_bp.route('/', methods=['POST'])
@require_role_decorator('admin')
def create_user():
    """
    Create a new user
    """
    data = request.get_json()
    user_id = data.get('user_id')
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    if not all([user_id, name, email, password, role]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (user_id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)", (user_id, name, email, password, role))
        conn.commit()
        return jsonify({"status": "success", "message": "User created"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()