from flask import Blueprint, jsonify, request
from db import get_db_connection
import mysql.connector
from auth import require_role_decorator, get_current_user

booking_bp = Blueprint("booking", __name__)


def get_request_json():
    data = request.get_json(silent=True)
    if data is None:
        return None, (
            jsonify({"status": "error", "message": "JSON body required"}),
            400,
        )
    return data, None


def fetch_booking(cursor, booking_id):
    cursor.execute(
        "SELECT booking_id, user_id, status, showtime_id FROM Booking WHERE booking_id = %s",
        (booking_id,),
    )
    return cursor.fetchone()


def fetch_payment(cursor, booking_id):
    cursor.execute(
        "SELECT payment_id, booking_id, amount, status, payment_date FROM Payment WHERE booking_id = %s",
        (booking_id,),
    )
    return cursor.fetchone()


@booking_bp.route("", methods=["POST"])
@require_role_decorator("customer")
def create_booking():
    """
    Create booking
    Insert into Booking and Booking_Seat
    Must respect UNIQUE(seat_number, theater_id, showtime_id)
    """
    data, error = get_request_json()
    if error:
        return error

    current_user_id, _ = get_current_user()
    showtime_id = data.get("showtime_id")
    seats = data.get("seats")  # list of seat_number

    if current_user_id is None or showtime_id is None or seats is None:
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    if not isinstance(seats, list) or not seats:
        return jsonify(
            {"status": "error", "message": "Seats must be a non-empty list"}
        ), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        cursor.execute(
            "SELECT theater_id FROM Showtime WHERE showtime_id = %s", (showtime_id,)
        )
        showtime = cursor.fetchone()
        if not showtime:
            conn.rollback()
            return jsonify({"status": "error", "message": "Showtime not found"}), 404
        theater_id = showtime["theater_id"]

        for seat in seats:
            cursor.execute(
                "SELECT seat_number FROM Seat WHERE seat_number = %s AND theater_id = %s FOR UPDATE",
                (seat, theater_id),
            )
            seat_row = cursor.fetchone()
            if not seat_row:
                conn.rollback()
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Seat {seat} not found in theater {theater_id}",
                    }
                ), 404

        placeholders = ",".join(["%s"] * len(seats))
        cursor.execute(
            f"SELECT seat_number FROM Booking_Seat WHERE seat_number IN ({placeholders}) AND showtime_id = %s",
            seats + [showtime_id],
        )
        booked = [row["seat_number"] for row in cursor.fetchall()]
        if booked:
            conn.rollback()
            return jsonify(
                {"status": "error", "message": f"Seats {booked} already booked"}
            ), 400

        cursor.execute(
            "SELECT COALESCE(MAX(booking_id), 0) + 1 AS next_id FROM Booking"
        )
        next_booking = cursor.fetchone()
        booking_id = next_booking["next_id"] if next_booking else 1
        cursor.execute(
            "INSERT INTO Booking (booking_id, user_id, showtime_id, status) VALUES (%s, %s, %s, 'Pending')",
            (booking_id, current_user_id, showtime_id),
        )

        for seat in seats:
            cursor.execute(
                "INSERT INTO Booking_Seat (booking_id, seat_number, theater_id, showtime_id) VALUES (%s, %s, %s, %s)",
                (booking_id, seat, theater_id, showtime_id),
            )
        conn.commit()
        return jsonify(
            {
                "status": "success",
                "message": "Booking created",
                "booking_id": booking_id,
            }
        ), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/<int:booking_id>/cancel", methods=["PUT"])
@require_role_decorator("customer")
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
        if booking["user_id"] != int(current_user_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        if booking["status"] == "Cancelled":
            return jsonify(
                {"status": "error", "message": "Booking already cancelled"}
            ), 400
        if booking["status"] == "Used":
            return jsonify(
                {
                    "status": "error",
                    "message": "Cannot cancel a booking that has already been used",
                }
            ), 400

        cursor.execute(
            "UPDATE Booking SET status = 'Cancelled' WHERE booking_id = %s",
            (booking_id,),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Booking cancelled"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/history", methods=["GET"])
@require_role_decorator("customer")
def get_booking_history():
    current_user_id, _ = get_current_user()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT b.booking_id,
               m.title,
               t.theater_name,
               st.show_date,
               st.price,
               b.status,
               COALESCE(p.status, 'NoPayment') AS payment_status,
               COALESCE(p.amount, COUNT(bs.seat_number) * st.price) AS total_amount
        FROM Booking b
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        JOIN Theater t ON st.theater_id = t.theater_id
        LEFT JOIN Payment p ON b.booking_id = p.booking_id
        JOIN Booking_Seat bs ON b.booking_id = bs.booking_id
        WHERE b.user_id = %s
        GROUP BY b.booking_id, m.title, t.theater_name, st.show_date, st.price, b.status, p.status, p.amount
        ORDER BY st.show_date DESC
    """,
        (current_user_id,),
    )
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": bookings})


@booking_bp.route("/<int:booking_id>/pay", methods=["POST"])
@require_role_decorator("customer")
def pay_booking(booking_id):
    current_user_id, _ = get_current_user()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT b.booking_id,
                   b.user_id,
                   b.status,
                   COUNT(bs.seat_number) AS seat_count,
                   st.price,
                   p.payment_id,
                   p.status AS payment_status
            FROM Booking b
            JOIN Showtime st ON b.showtime_id = st.showtime_id
            LEFT JOIN Booking_Seat bs ON b.booking_id = bs.booking_id
            LEFT JOIN Payment p ON b.booking_id = p.booking_id
            WHERE b.booking_id = %s
            GROUP BY b.booking_id, b.user_id, b.status, st.price, p.payment_id, p.status
        """,
            (booking_id,),
        )
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking["user_id"] != int(current_user_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        if booking["status"] == "Cancelled":
            return jsonify(
                {"status": "error", "message": "Cannot pay a cancelled booking"}
            ), 400
        if booking["payment_status"] == "Confirmed":
            return jsonify({"status": "success", "message": "Booking already paid"})

        amount = booking["seat_count"] * booking["price"]
        if booking["payment_id"]:
            cursor.execute(
                "UPDATE Payment SET amount = %s, status = 'Confirmed' WHERE payment_id = %s",
                (amount, booking["payment_id"]),
            )
        else:
            cursor.execute(
                "SELECT COALESCE(MAX(payment_id), 0) + 1 AS next_id FROM Payment"
            )
            next_payment = cursor.fetchone()
            payment_id = next_payment["next_id"] if next_payment else 1
            cursor.execute(
                "INSERT INTO Payment (payment_id, booking_id, amount, status) VALUES (%s, %s, %s, 'Confirmed')",
                (payment_id, booking_id, amount),
            )

        cursor.execute(
            "UPDATE Booking SET status = 'Confirmed' WHERE booking_id = %s",
            (booking_id,),
        )
        conn.commit()
        return jsonify(
            {
                "status": "success",
                "message": "Payment confirmed",
                "booking_id": booking_id,
            }
        )
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/payments/<int:booking_id>", methods=["GET"])
@require_role_decorator(["customer", "staff", "admin"])
def get_payment_history(booking_id):
    current_user_id, role = get_current_user()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT p.payment_id, p.booking_id, p.amount, p.status, p.payment_date, b.user_id
        FROM Payment p
        JOIN Booking b ON p.booking_id = b.booking_id
        WHERE p.booking_id = %s
    """,
        (booking_id,),
    )
    payment = cursor.fetchone()
    cursor.close()
    conn.close()
    if not payment:
        return jsonify({"status": "error", "message": "Payment not found"}), 404
    if role == "customer" and int(current_user_id) != payment["user_id"]:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    payment.pop("user_id", None)
    return jsonify({"status": "success", "data": payment})


@booking_bp.route("/user/<int:user_id>", methods=["GET"])
@require_role_decorator("customer")
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


@booking_bp.route("/pending/<int:user_id>", methods=["GET"])
@require_role_decorator("customer")
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
    cursor.execute(
        """
        SELECT u.user_id, COUNT(bd.booking_id) AS total_bookings, COALESCE(SUM(bd.total_price), 0) AS total_pending
        FROM Users u
        LEFT JOIN Booking_Detail bd 
            ON u.user_id = bd.user_id 
            AND bd.status = 'Pending'
        WHERE u.role = 'customer' AND u.user_id = %s
        GROUP BY u.user_id
    """,
        (user_id,),
    )
    pending = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": pending})


@booking_bp.route("", methods=["GET"])
@require_role_decorator(["staff", "admin"])
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


@booking_bp.route("/<int:booking_id>", methods=["GET"])
@require_role_decorator(["customer", "staff", "admin"])
def get_booking(booking_id):
    """
    Get booking detail for customer or staff
    """
    current_user_id, role = get_current_user()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT b.booking_id,
               b.user_id,
               b.showtime_id,
               b.status,
               b.booking_date,
               m.title,
               t.theater_name,
               st.show_date AS show_date,
               st.price
        FROM Booking b
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        JOIN Theater t ON st.theater_id = t.theater_id
        WHERE b.booking_id = %s
    """,
        (booking_id,),
    )
    booking = cursor.fetchone()
    cursor.close()
    conn.close()
    if not booking:
        return jsonify({"status": "error", "message": "Booking not found"}), 404
    if role == "customer" and int(current_user_id) != booking["user_id"]:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    return jsonify({"status": "success", "data": booking})


@booking_bp.route("/<int:booking_id>", methods=["PUT"])
@require_role_decorator("customer")
def update_booking(booking_id):
    """
    Update a booking's showtime or seats
    """
    data, error = get_request_json()
    if error:
        return error

    showtime_id = data.get("showtime_id")
    seats = data.get("seats")
    if showtime_id is None and seats is None:
        return jsonify({"status": "error", "message": "Nothing to update"}), 400

    current_user_id, _ = get_current_user()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking["user_id"] != int(current_user_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        if booking["status"] in ["Cancelled", "Used"]:
            return jsonify(
                {
                    "status": "error",
                    "message": "Cannot update a cancelled or used booking",
                }
            ), 400

        target_showtime_id = booking["showtime_id"]
        if showtime_id is not None:
            if showtime_id != booking["showtime_id"] and seats is None:
                return jsonify(
                    {
                        "status": "error",
                        "message": "Changing showtime requires new seats",
                    }
                ), 400
            cursor.execute(
                "SELECT theater_id FROM Showtime WHERE showtime_id = %s", (showtime_id,)
            )
            showtime = cursor.fetchone()
            if not showtime:
                return jsonify(
                    {"status": "error", "message": "Target showtime not found"}
                ), 404
            target_showtime_id = showtime_id
            target_theater_id = showtime["theater_id"]
        else:
            cursor.execute(
                "SELECT theater_id FROM Showtime WHERE showtime_id = %s",
                (booking["showtime_id"],),
            )
            showtime = cursor.fetchone()
            target_theater_id = showtime["theater_id"]

        if seats is not None:
            if not isinstance(seats, list) or not seats:
                return jsonify(
                    {"status": "error", "message": "Seats must be a non-empty list"}
                ), 400
            for seat in seats:
                cursor.execute(
                    "SELECT seat_number FROM Seat WHERE seat_number = %s AND theater_id = %s FOR UPDATE",
                    (seat, target_theater_id),
                )
                if cursor.fetchone() is None:
                    return jsonify(
                        {
                            "status": "error",
                            "message": f"Seat {seat} does not exist in theater",
                        }
                    ), 400
            placeholders = ",".join(["%s"] * len(seats))
            cursor.execute(
                f"SELECT seat_number FROM Booking_Seat WHERE seat_number IN ({placeholders}) AND showtime_id = %s AND booking_id != %s",
                seats + [target_showtime_id, booking_id],
            )
            booked = [row["seat_number"] for row in cursor.fetchall()]
            if booked:
                return jsonify(
                    {"status": "error", "message": f"Seats {booked} already booked"}
                ), 400

            cursor.execute(
                "DELETE FROM Booking_Seat WHERE booking_id = %s", (booking_id,)
            )
            for seat in seats:
                cursor.execute(
                    "INSERT INTO Booking_Seat (booking_id, seat_number, theater_id, showtime_id) VALUES (%s, %s, %s, %s)",
                    (booking_id, seat, target_theater_id, target_showtime_id),
                )

        if showtime_id is not None and showtime_id != booking["showtime_id"]:
            cursor.execute(
                "UPDATE Booking SET showtime_id = %s WHERE booking_id = %s",
                (showtime_id, booking_id),
            )

        cursor.execute(
            "SELECT payment_id FROM Payment WHERE booking_id = %s", (booking_id,)
        )
        payment_row = cursor.fetchone()
        if payment_row:
            cursor.execute(
                "SELECT COUNT(bs.seat_number) * st.price AS total_price FROM Booking_Seat bs JOIN Showtime st ON bs.showtime_id = st.showtime_id WHERE bs.booking_id = %s GROUP BY bs.showtime_id, st.price",
                (booking_id,),
            )
            payment_total = cursor.fetchone()
            if payment_total:
                cursor.execute(
                    "UPDATE Payment SET amount = %s WHERE payment_id = %s",
                    (payment_total["total_price"], payment_row["payment_id"]),
                )

        conn.commit()
        return jsonify({"status": "success", "message": "Booking updated"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/<int:booking_id>/status", methods=["PUT"])
@require_role_decorator(["staff", "admin"])
def update_booking_status(booking_id):
    """
    Update booking status
    """
    data, error = get_request_json()
    if error:
        return error

    status = data.get("status")
    if not status:
        return jsonify({"status": "error", "message": "Status required"}), 400
    allowed_status = ["Pending", "Confirmed", "Cancelled", "Used"]
    if status not in allowed_status:
        return jsonify(
            {"status": "error", "message": f"Invalid status. Allowed: {allowed_status}"}
        ), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404

        cursor.execute(
            "UPDATE Booking SET status = %s WHERE booking_id = %s", (status, booking_id)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Status updated"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/<int:booking_id>/use", methods=["PUT"])
@require_role_decorator(["staff", "admin"])
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
        if booking["status"] == "Cancelled":
            return jsonify(
                {"status": "error", "message": "Cannot use a cancelled booking"}
            ), 400
        if booking["status"] == "Used":
            return jsonify(
                {"status": "error", "message": "Booking is already marked as used"}
            ), 400

        cursor.execute(
            "UPDATE Booking SET status = 'Used' WHERE booking_id = %s", (booking_id,)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Booking marked as used"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/payments", methods=["POST"])
@require_role_decorator("customer")
def create_payment():
    """
    Create payment
    """
    current_user_id, _ = get_current_user()

    data, error = get_request_json()
    if error:
        return error

    booking_id = data.get("booking_id")
    if booking_id is None:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking["user_id"] != int(current_user_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403

        cursor.execute(
            "SELECT payment_id FROM Payment WHERE booking_id = %s", (booking_id,)
        )
        if cursor.fetchone() is not None:
            return jsonify(
                {"status": "error", "message": "Payment already exists"}
            ), 400

        cursor.execute(
            """
            SELECT b.booking_id, COUNT(bs.seat_number) * st.price AS total_price
            FROM Booking b
            JOIN Showtime st ON b.showtime_id = st.showtime_id
            JOIN Booking_Seat bs ON b.booking_id = bs.booking_id
            WHERE b.booking_id = %s
            GROUP BY b.booking_id, st.price
        """,
            (booking_id,),
        )
        booking_row = cursor.fetchone()
        if not booking_row:
            return jsonify({"status": "error", "message": "Booking not found"}), 404

        amount = booking_row["total_price"]
        status = "Pending"

        cursor.execute(
            "SELECT COALESCE(MAX(payment_id), 0) + 1 AS next_id FROM Payment"
        )
        next_payment = cursor.fetchone()
        payment_id = next_payment["next_id"] if next_payment else 1
        cursor.execute(
            "INSERT INTO Payment (payment_id, booking_id, amount, status) VALUES (%s, %s, %s, %s)",
            (payment_id, booking_id, amount, status),
        )
        cursor.execute(
            "UPDATE Booking SET status = 'Confirmed' WHERE booking_id = %s",
            (booking_id,),
        )
        conn.commit()
        return jsonify(
            {
                "status": "success",
                "message": "Payment created",
                "payment_id": payment_id,
            }
        ), 201
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/payments/<int:booking_id>/refund", methods=["PUT"])
@require_role_decorator("admin")
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
        if payment["status"] == "Refunded":
            return jsonify(
                {"status": "error", "message": "Payment already refunded"}
            ), 400
        if payment["status"] != "Confirmed":
            return jsonify(
                {
                    "status": "error",
                    "message": "Only confirmed payments can be refunded",
                }
            ), 400

        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
        if booking["status"] == "Used":
            return jsonify(
                {"status": "error", "message": "Cannot refund a used booking"}
            ), 400

        cursor.execute(
            "UPDATE Payment SET status = 'Refunded' WHERE booking_id = %s",
            (booking_id,),
        )
        cursor.execute(
            "UPDATE Booking SET status = 'Cancelled' WHERE booking_id = %s",
            (booking_id,),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Payment refunded"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/staff/<int:booking_id>", methods=["GET"])
@require_role_decorator(["staff", "admin"])
def staff_check_booking(booking_id):
    """
    Staff check booking status
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT b.booking_id, u.name, m.title, st.show_date, b.status
        FROM Booking b
        JOIN Users u ON b.user_id = u.user_id
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        WHERE b.booking_id = %s
    """,
        (booking_id,),
    )
    booking = cursor.fetchone()
    cursor.close()
    conn.close()
    if booking:
        return jsonify({"status": "success", "data": booking})
    else:
        return jsonify({"status": "error", "message": "Booking not found"}), 404


@booking_bp.route("/staff/<int:booking_id>/status", methods=["PUT"])
@require_role_decorator(["staff", "admin"])
def staff_update_status(booking_id):
    """
    Staff update booking status
    """
    data, error = get_request_json()
    if error:
        return error

    status = data.get("status")
    if not status:
        return jsonify({"status": "error", "message": "Status required"}), 400
    # Validate status
    allowed_status = ["Pending", "Confirmed", "Cancelled", "Used"]
    if status not in allowed_status:
        return jsonify(
            {"status": "error", "message": f"Invalid status. Allowed: {allowed_status}"}
        ), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        booking = fetch_booking(cursor, booking_id)
        if not booking:
            return jsonify({"status": "error", "message": "Booking not found"}), 404

        cursor.execute(
            "UPDATE Booking SET status = %s WHERE booking_id = %s", (status, booking_id)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Status updated"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
