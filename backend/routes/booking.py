from flask import Blueprint, jsonify, request
from db import get_db_connection
import mysql.connector

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('', methods=['POST'])
def create_booking():
    """
    Create booking
    Insert into Booking and Booking_Seat
    Must respect UNIQUE(seat_number, theater_id, showtime_id)
    """
    data = request.get_json()
    user_id = data.get('user_id')
    showtime_id = data.get('showtime_id')
    seats = data.get('seats')  # list of seat_number
    total_price = data.get('total_price')
    booking_id = data.get('booking_id')  # assume provided
    if not all([user_id, showtime_id, seats, total_price, booking_id]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get theater_id
        cursor.execute("SELECT theater_id FROM Showtime WHERE showtime_id = %s", (showtime_id,))
        showtime = cursor.fetchone()
        if not showtime:
            conn.rollback()
            return jsonify({"status": "error", "message": "Showtime not found"}), 404
        theater_id = showtime['theater_id']
        # Check available seats
        cursor.execute("SELECT seat_number FROM Available_Seats WHERE showtime_id = %s AND theater_id = %s", (showtime_id, theater_id))
        available = [row['seat_number'] for row in cursor.fetchall()]
        for seat in seats:
            if str(seat) not in [str(s) for s in available]:
                conn.rollback()
                return jsonify({"status": "error", "message": f"Seat {seat} not available"}), 400
        # Insert booking
        cursor.execute("INSERT INTO Booking (booking_id, user_id, showtime_id, total_price) VALUES (%s, %s, %s, %s)", (booking_id, user_id, showtime_id, total_price))
        # Insert seats
        for seat in seats:
            cursor.execute("INSERT INTO Booking_Seat (booking_id, seat_number, theater_id, showtime_id) VALUES (%s, %s, %s, %s)", (booking_id, seat, theater_id, showtime_id))
        conn.commit()
        return jsonify({"status": "success", "message": "Booking created", "booking_id": booking_id})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
def cancel_booking(booking_id):
    """
    Cancel booking
    UPDATE Booking SET status = 'Cancelled'
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Booking SET status = 'Cancelled' WHERE booking_id = %s", (booking_id,))
    conn.commit()
    if cursor.rowcount > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Booking cancelled"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Booking not found"}), 404

@booking_bp.route('/user/<int:user_id>', methods=['GET'])
def get_bookings_by_user(user_id):
    """
    Get booking by user
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Booking WHERE user_id = %s", (user_id,))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": bookings})

@booking_bp.route('/pending/<int:user_id>', methods=['GET'])
def get_pending_summary(user_id):
    """
    Get pending payment summary
    Uses query from 3_queries.sql
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, COUNT(bd.booking_id) AS total_bookings, COALESCE(SUM(bd.total_price), 0) AS total_pending
        FROM Users u
        LEFT JOIN Booking_Detail bd 
            ON u.user_id = bd.user_id 
            AND bd.status = 'Pending'
        WHERE u.role = 'customer' AND u.user_id = %s
        GROUP BY u.user_id
    """, (user_id,))
    pending = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": pending})

@booking_bp.route('', methods=['GET'])
def get_bookings():
    """
    Get all bookings
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Booking")
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": bookings})

@booking_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """
    Get booking detail
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Booking WHERE booking_id = %s", (booking_id,))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()
    if booking:
        return jsonify({"status": "success", "data": booking})
    else:
        return jsonify({"status": "error", "message": "Booking not found"}), 404

@booking_bp.route('/<int:booking_id>/status', methods=['PUT'])
def update_booking_status(booking_id):
    """
    Update booking status
    """
    data = request.get_json()
    status = data.get('status')
    if not status:
        return jsonify({"status": "error", "message": "Status required"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Booking SET status = %s WHERE booking_id = %s", (status, booking_id))
    conn.commit()
    if cursor.rowcount > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Status updated"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Booking not found"}), 404

@booking_bp.route('/<int:booking_id>/use', methods=['PUT'])
def use_booking(booking_id):
    """
    Mark booking as Used
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Booking SET status = 'Used' WHERE booking_id = %s", (booking_id,))
    conn.commit()
    if cursor.rowcount > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Booking marked as used"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Booking not found"}), 404

@booking_bp.route('/payments', methods=['POST'])
def create_payment():
    """
    Create payment
    """
    data = request.get_json()
    payment_id = data.get('payment_id')
    booking_id = data.get('booking_id')
    amount = data.get('amount')
    status = data.get('status', 'Pending')
    if not all([payment_id, booking_id, amount]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Payment (payment_id, booking_id, amount, status) VALUES (%s, %s, %s, %s)", (payment_id, booking_id, amount, status))
        conn.commit()
        return jsonify({"status": "success", "message": "Payment created"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/payments/<int:booking_id>/refund', methods=['PUT'])
def refund_payment(booking_id):
    """
    Refund booking
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Payment SET status = 'Refunded' WHERE booking_id = %s", (booking_id,))
        cursor.execute("UPDATE Booking SET status = 'Cancelled' WHERE booking_id = %s", (booking_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Refunded"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/staff/<int:booking_id>', methods=['GET'])
def staff_check_booking(booking_id):
    """
    Staff check booking status
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.booking_id, u.name, m.title, st.show_date, b.status
        FROM Booking b
        JOIN Users u ON b.user_id = u.user_id
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        WHERE b.booking_id = %s
    """, (booking_id,))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()
    if booking:
        return jsonify({"status": "success", "data": booking})
    else:
        return jsonify({"status": "error", "message": "Booking not found"}), 404

@booking_bp.route('/staff/<int:booking_id>/status', methods=['PUT'])
def staff_update_status(booking_id):
    """
    Staff update booking status
    """
    data = request.get_json()
    status = data.get('status')
    if not status:
        return jsonify({"status": "error", "message": "Status required"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Booking SET status = %s WHERE booking_id = %s", (status, booking_id))
    conn.commit()
    if cursor.rowcount > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Status updated"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Booking not found"}), 404