from flask import Blueprint, jsonify, request
from db import get_db_connection
import mysql.connector
from auth import require_role_decorator, get_current_user

booking_bp = Blueprint('booking', __name__)

def get_request_json():
    data = request.get_json(silent=True)
    if data is None:
        return None, jsonify({"status": "error", "message": "JSON body required"}), 400
    return data, None

def fetch_booking(cursor, booking_id):
    cursor.execute("SELECT booking_id, status FROM Booking WHERE booking_id = %s", (booking_id,))
    return cursor.fetchone()

def fetch_payment(cursor, booking_id):
    cursor.execute("SELECT payment_id, status FROM Payment WHERE booking_id = %s", (booking_id,))
    return cursor.fetchone()

@booking_bp.route('', methods=['POST'])
@require_role_decorator('customer')
def create_booking():
    """
    Create booking
    Insert into Booking and Booking_Seat
    Must respect UNIQUE(seat_number, theater_id, showtime_id)
    """
    data, error = get_request_json()
    if error:
        return error

    user_id = data.get('user_id')
    showtime_id = data.get('showtime_id')
    seats = data.get('seats')  # list of seat_number

    if user_id is None or showtime_id is None or seats is None:
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    if not isinstance(seats, list) or not seats:
        return jsonify({"status": "error", "message": "Seats must be a non-empty list"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        # Get theater_id
        cursor.execute("SELECT theater_id FROM Showtime WHERE showtime_id = %s", (showtime_id,))
        showtime = cursor.fetchone()
        if not showtime:
            conn.rollback()
            return jsonify({"status": "error", "message": "Showtime not found"}), 404
        theater_id = showtime['theater_id']

        # Lock seats for update
        for seat in seats:
            cursor.execute("SELECT seat_number FROM Seat WHERE seat_number = %s AND theater_id = %s FOR UPDATE", (seat, theater_id))

        # Check if seats are already booked
        if seats:
            placeholders = ','.join(['%s'] * len(seats))
            cursor.execute(f"SELECT seat_number FROM Booking_Seat WHERE seat_number IN ({placeholders}) AND showtime_id = %s", seats + [showtime_id])
            booked = [row['seat_number'] for row in cursor.fetchall()]
            if booked:
                conn.rollback()
                return jsonify({"status": "error", "message": f"Seats {booked} already booked"}), 400

        # Insert booking with status Pending
        cursor.execute("SELECT COALESCE(MAX(booking_id), 0) + 1 AS next_id FROM Booking")
        next_booking = cursor.fetchone()
        booking_id = next_booking['next_id'] if next_booking else 1
        cursor.execute(
            "INSERT INTO Booking (booking_id, user_id, showtime_id, status) VALUES (%s, %s, %s, 'Pending')",
            (booking_id, user_id, showtime_id),
        )

        # Insert seats
        for seat in seats:
            cursor.execute(
                "INSERT INTO Booking_Seat (booking_id, seat_number, theater_id, showtime_id) VALUES (%s, %s, %s, %s)",
                (booking_id, seat, theater_id, showtime_id),
            )
        conn.commit()
        return jsonify({"status": "success", "message": "Booking created", "booking_id": booking_id}), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
@require_role_decorator('customer')
def cancel_booking(booking_id):
    """
    Cancel booking
    UPDATE Booking SET status = 'Cancelled'
    """
    current_user_id, _ = get_current_user()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking['user_id'] != int(current_user_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        if booking['status'] == 'Cancelled':
            return jsonify({"status": "error", "message": "Booking already cancelled"}), 400
        if booking['status'] == 'Used':
            return jsonify({"status": "error", "message": "Cannot cancel a booking that has already been used"}), 400

        cursor.execute("UPDATE Booking SET status = 'Cancelled' WHERE booking_id = %s", (booking_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Booking cancelled"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/user/<int:user_id>', methods=['GET'])
@require_role_decorator('customer')
def get_bookings_by_user(user_id):
    """
    Get booking by user
    """
    current_user_id, _ = get_current_user()
    if int(current_user_id) != user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Booking WHERE user_id = %s", (user_id,))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": bookings})

@booking_bp.route('/pending/<int:user_id>', methods=['GET'])
@require_role_decorator('customer')
def get_pending_summary(user_id):
    """
    Get pending payment summary
    Uses query from 3_queries.sql
    """
    current_user_id, _ = get_current_user()
    if int(current_user_id) != user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

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
@require_role_decorator(['staff', 'admin'])
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
@require_role_decorator(['staff', 'admin'])
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
@require_role_decorator(['staff', 'admin'])
def update_booking_status(booking_id):
    """
    Update booking status
    """
    data, error = get_request_json()
    if error:
        return error

    status = data.get('status')
    if not status:
        return jsonify({"status": "error", "message": "Status required"}), 400
    allowed_status = ['Pending','Confirmed','Cancelled','Used']
    if status not in allowed_status:
        return jsonify({
        "status": "error",
        "message": f"Invalid status. Allowed: {allowed_status}"
        }), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404

        cursor.execute("UPDATE Booking SET status = %s WHERE booking_id = %s", (status, booking_id))
        conn.commit()
        return jsonify({"status": "success", "message": "Status updated"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/<int:booking_id>/use', methods=['PUT'])
@require_role_decorator(['staff', 'admin'])
def use_booking(booking_id):
    """
    Mark booking as Used
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking['status'] == 'Cancelled':
            return jsonify({"status": "error", "message": "Cannot use a cancelled booking"}), 400
        if booking['status'] == 'Used':
            return jsonify({"status": "error", "message": "Booking is already marked as used"}), 400

        cursor.execute("UPDATE Booking SET status = 'Used' WHERE booking_id = %s", (booking_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Booking marked as used"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/payments', methods=['POST'])
@require_role_decorator('customer')
def create_payment():
    """
    Create payment
    """
    current_user_id, _ = get_current_user()

    data, error = get_request_json()
    if error:
        return error

    booking_id = data.get('booking_id')
    if booking_id is None:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking['user_id'] != int(current_user_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403

        cursor.execute("SELECT payment_id FROM Payment WHERE booking_id = %s", (booking_id,))
        if cursor.fetchone() is not None:
            return jsonify({"status": "error", "message": "Payment already exists"}), 400

        cursor.execute("""
            SELECT b.booking_id, COUNT(bs.seat_number) * st.price AS total_price
            FROM Booking b
            JOIN Showtime st ON b.showtime_id = st.showtime_id
            JOIN Booking_Seat bs ON b.booking_id = bs.booking_id
            WHERE b.booking_id = %s
            GROUP BY b.booking_id, st.price
        """, (booking_id,))
        booking_row = cursor.fetchone()
        if not booking_row:
            return jsonify({"status": "error", "message": "Booking not found"}), 404

        amount = booking_row['total_price']
        status = 'Pending'

        cursor.execute("SELECT COALESCE(MAX(payment_id), 0) + 1 AS next_id FROM Payment")
        next_payment = cursor.fetchone()
        payment_id = next_payment['next_id'] if next_payment else 1
        cursor.execute(
            "INSERT INTO Payment (payment_id, booking_id, amount, status) VALUES (%s, %s, %s, %s)",
            (payment_id, booking_id, amount, status),
        )
        cursor.execute("UPDATE Booking SET status = 'Confirmed' WHERE booking_id = %s", (booking_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Payment created", "payment_id": payment_id}), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/payments/<int:booking_id>/refund', methods=['PUT'])
@require_role_decorator('admin')
def refund_payment(booking_id):
    """
    Refund booking
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        payment = fetch_payment(cursor, booking_id)
        if not payment:
            return jsonify({"status": "error", "message": "Payment not found"}), 404
        if payment['status'] == 'Refunded':
            return jsonify({"status": "error", "message": "Payment already refunded"}), 400
        if payment['status'] != 'Confirmed':
            return jsonify({"status": "error", "message": "Only confirmed payments can be refunded"}), 400

        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking['status'] == 'Used':
            return jsonify({"status": "error", "message": "Cannot refund a used booking"}), 400

        cursor.execute("UPDATE Payment SET status = 'Refunded' WHERE booking_id = %s", (booking_id,))
        cursor.execute("UPDATE Booking SET status = 'Cancelled' WHERE booking_id = %s", (booking_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Payment refunded"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@booking_bp.route('/staff/<int:booking_id>', methods=['GET'])
@require_role_decorator(['staff', 'admin'])
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
@require_role_decorator(['staff', 'admin'])
def staff_update_status(booking_id):
    """
    Staff update booking status
    """
    data, error = get_request_json()
    if error:
        return error

    status = data.get('status')
    if not status:
        return jsonify({"status": "error", "message": "Status required"}), 400
    # Validate status
    allowed_status = ['Pending', 'Confirmed', 'Cancelled', 'Used']
    if status not in allowed_status:
        return jsonify({"status": "error", "message": f"Invalid status. Allowed: {allowed_status}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404

        cursor.execute("UPDATE Booking SET status = %s WHERE booking_id = %s", (status, booking_id))
        conn.commit()
        return jsonify({"status": "success", "message": "Status updated"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
