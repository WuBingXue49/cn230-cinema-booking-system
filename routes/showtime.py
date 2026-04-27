from flask import Blueprint, jsonify, request
from db import get_db_connection
import mysql.connector
from auth import require_role_decorator

showtime_bp = Blueprint("showtime", __name__)


@showtime_bp.route("", methods=["GET"])
def get_showtime():
    """
    Get showtimes with optional filters
    """
    title = request.args.get("title")
    theater = request.args.get("theater")
    show_date = request.args.get("show_date")
    query = """
        SELECT showtime_id, title, theater_name, show_date, price, GROUP_CONCAT(seat_number ORDER BY seat_number SEPARATOR ', ') AS seats
        FROM Showtime_Detail
    """
    filters = []
    params = []
    if title:
        filters.append("title LIKE %s")
        params.append(f"%{title}%")
    if theater:
        filters.append("theater_name LIKE %s")
        params.append(f"%{theater}%")
    if show_date:
        filters.append("DATE(show_date) = %s")
        params.append(show_date)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " GROUP BY showtime_id, title, theater_name, show_date, price"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    showtimes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": showtimes})


@showtime_bp.route("/<int:showtime_id>", methods=["GET"])
def get_showtime_by_id(showtime_id):
    """
    Get specific showtime
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Showtime WHERE showtime_id = %s", (showtime_id,))
    showtime = cursor.fetchone()
    cursor.close()
    conn.close()
    if showtime:
        return jsonify({"status": "success", "data": showtime})
    else:
        return jsonify({"status": "error", "message": "Showtime not found"}), 404


@showtime_bp.route("/<int:showtime_id>/available-seats", methods=["GET"])
def get_available_seats(showtime_id):
    """
    Get available seats for a showtime
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT seat_number FROM Available_Seats WHERE showtime_id = %s", (showtime_id,)
    )
    seats = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": seats})


@showtime_bp.route("/<int:showtime_id>/layout", methods=["GET"])
def get_showtime_layout(showtime_id):
    """
    Get seat layout and inventory for a showtime
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT theater_id FROM Showtime WHERE showtime_id = %s", (showtime_id,)
    )
    showtime = cursor.fetchone()
    if not showtime:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Showtime not found"}), 404

    theater_id = showtime["theater_id"]
    cursor.execute(
        """
        SELECT s.seat_number,
               CASE WHEN EXISTS(
                   SELECT 1
                   FROM Booking_Seat bs
                   JOIN Booking b ON bs.booking_id = b.booking_id
                   WHERE bs.showtime_id = %s
                     AND bs.seat_number = s.seat_number
                     AND bs.theater_id = s.theater_id
                     AND b.status IN ('Pending','Confirmed')
               ) THEN 'Booked' ELSE 'Available' END AS status
        FROM Seat s
        WHERE s.theater_id = %s
        ORDER BY s.seat_number
    """,
        (showtime_id, theater_id),
    )
    layout = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": layout})


@showtime_bp.route("", methods=["POST"])
@require_role_decorator("admin")
def create_showtime():
    """
    Admin create showtime
    """
    data = request.get_json()
    showtime_id = data.get("showtime_id")
    movie_id = data.get("movie_id")
    theater_id = data.get("theater_id")
    show_date = data.get("show_date")
    price = data.get("price")
    if not all([showtime_id, movie_id, theater_id, show_date, price]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Showtime (showtime_id, movie_id, theater_id, show_date, price) VALUES (%s, %s, %s, %s, %s)",
            (showtime_id, movie_id, theater_id, show_date, price),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Showtime created"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@showtime_bp.route("/<int:showtime_id>", methods=["PUT"])
@require_role_decorator("admin")
def update_showtime(showtime_id):
    """
    Admin update showtime
    """
    data = request.get_json()
    movie_id = data.get("movie_id")
    theater_id = data.get("theater_id")
    show_date = data.get("show_date")
    price = data.get("price")
    if not all([movie_id, theater_id, show_date, price]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Showtime SET movie_id = %s, theater_id = %s, show_date = %s, price = %s WHERE showtime_id = %s",
        (movie_id, theater_id, show_date, price, showtime_id),
    )
    conn.commit()
    if cursor.rowcount > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Showtime updated"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Showtime not found"}), 404


@showtime_bp.route("/<int:showtime_id>", methods=["DELETE"])
@require_role_decorator("admin")
def delete_showtime(showtime_id):
    """
    Admin delete showtime
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Showtime WHERE showtime_id = %s", (showtime_id,))
    conn.commit()
    if cursor.rowcount > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Showtime deleted"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Showtime not found"}), 404
