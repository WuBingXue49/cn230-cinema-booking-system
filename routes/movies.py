from flask import Blueprint, jsonify
from db import get_db_connection
from auth import require_role_decorator

movies_bp = Blueprint('movies', __name__)

@movies_bp.route('/genres', methods=['GET'])
def get_movie_genres():
    """
    Get movie genres
    Uses Movie + Movie_Genre with aggregation
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.movie_id, m.title, GROUP_CONCAT(mg.genre ORDER BY mg.genre SEPARATOR ', ') AS genres
        FROM Movie m
        JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
        GROUP BY m.movie_id, m.title
    """)
    genres = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": genres})

@movies_bp.route('/top', methods=['GET'])
def get_top_movie():
    """
    Get top selling movie
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.movie_id, m.title, SUM(p.amount) AS total_revenue
        FROM Payment p
        JOIN Booking b ON p.booking_id = b.booking_id
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        WHERE p.status = 'Confirmed'
        GROUP BY m.movie_id, m.title
        ORDER BY total_revenue DESC
        LIMIT 1
    """)
    top = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": top})

@movies_bp.route('/revenue', methods=['GET'])
#@require_role_decorator(['staff', 'admin'])
def get_movie_revenue():
    """
    Get revenue per movie
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.movie_id, m.title, SUM(p.amount) AS total_revenue
        FROM Payment p
        JOIN Booking b ON p.booking_id = b.booking_id
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        WHERE p.status = 'Confirmed'
        GROUP BY m.movie_id, m.title
        ORDER BY total_revenue DESC
    """)
    revenue = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": revenue})

@movies_bp.route('/<title>/seats', methods=['GET'])
def get_movie_seats(title):
    """
    Get showtime + available seats by movie title
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT showtime_id, title, theater_name, show_date, price, GROUP_CONCAT(seat_number ORDER BY seat_number SEPARATOR ', ') AS seats
        FROM Showtime_Detail
        WHERE title = %s
        GROUP BY showtime_id, title, theater_name, show_date, price
    """, (title,))
    showtimes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": showtimes})

@movies_bp.route('/admin/revenue/<int:movie_id>', methods=['GET'])
@require_role_decorator(['admin'])
def get_revenue_by_movie(movie_id):
    """
    Admin get revenue for specific movie
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.movie_id, m.title, SUM(p.amount) AS total_revenue
        FROM Payment p
        JOIN Booking b ON p.booking_id = b.booking_id
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        WHERE m.movie_id = %s
        GROUP BY m.movie_id, m.title
    """, (movie_id,))
    revenue = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": revenue})

@movies_bp.route("/", methods=["GET"])
def get_movies():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT movie_id, title FROM Movie")
    movies = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"status": "success", "data": movies})
