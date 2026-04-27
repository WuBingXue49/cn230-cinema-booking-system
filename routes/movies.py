from flask import Blueprint, jsonify, request
from db import get_db_connection
from auth import require_role_decorator

movies_bp = Blueprint("movies", __name__)


def get_movie_columns():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW COLUMNS FROM Movie")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return columns


@movies_bp.route("/genres", methods=["GET"])
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


@movies_bp.route("/top", methods=["GET"])
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


@movies_bp.route("/search", methods=["GET"])
def search_movies():
    title = request.args.get("title")
    genre = request.args.get("genre")
    producer = request.args.get("producer")

    query = """
        SELECT DISTINCT m.movie_id, m.title, m.duration, p.owner_name AS producer
        FROM Movie m
        LEFT JOIN Producer p ON m.owner_id = p.owner_id
        LEFT JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
    """
    filters = []
    params = []
    if title:
        filters.append("m.title LIKE %s")
        params.append(f"%{title}%")
    if genre:
        filters.append("mg.genre LIKE %s")
        params.append(f"%{genre}%")
    if producer:
        filters.append("p.owner_name LIKE %s")
        params.append(f"%{producer}%")
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY m.title"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": movies})


@movies_bp.route("/<int:movie_id>", methods=["GET"])
def get_movie_detail(movie_id):
    columns = ["movie_id", "owner_id", "title", "duration"]
    extra_columns = [
        col
        for col in ["description", "poster_url", "rating"]
        if col in get_movie_columns()
    ]
    columns.extend(extra_columns)
    column_sql = ", ".join(
        [f"m.{col}" for col in columns] + ["p.owner_name AS producer"]
    )

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        f"SELECT {column_sql} FROM Movie m LEFT JOIN Producer p ON m.owner_id = p.owner_id WHERE m.movie_id = %s",
        (movie_id,),
    )
    movie = cursor.fetchone()
    if movie:
        cursor.execute("SELECT genre FROM Movie_Genre WHERE movie_id = %s", (movie_id,))
        movie["genres"] = [row["genre"] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    if movie:
        return jsonify({"status": "success", "data": movie})
    return jsonify({"status": "error", "message": "Movie not found"}), 404


@movies_bp.route("/revenue", methods=["GET"])
# @require_role_decorator(['staff', 'admin'])
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


@movies_bp.route("/<title>/seats", methods=["GET"])
def get_movie_seats(title):
    """
    Get showtime + available seats by movie title
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT showtime_id, title, theater_name, show_date, price, GROUP_CONCAT(seat_number ORDER BY seat_number SEPARATOR ', ') AS seats
        FROM Showtime_Detail
        WHERE title = %s
        GROUP BY showtime_id, title, theater_name, show_date, price
    """,
        (title,),
    )
    showtimes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": showtimes})


@movies_bp.route("/admin/revenue/<int:movie_id>", methods=["GET"])
@require_role_decorator(["admin"])
def get_revenue_by_movie(movie_id):
    """
    Admin get revenue for specific movie
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT m.movie_id, m.title, SUM(p.amount) AS total_revenue
        FROM Payment p
        JOIN Booking b ON p.booking_id = b.booking_id
        JOIN Showtime st ON b.showtime_id = st.showtime_id
        JOIN Movie m ON st.movie_id = m.movie_id
        WHERE m.movie_id = %s
        GROUP BY m.movie_id, m.title
    """,
        (movie_id,),
    )
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


@movies_bp.route("/admin/<int:movie_id>", methods=["PUT"])
@require_role_decorator("admin")
def update_movie(movie_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSON body required"}), 400

    allowed = ["title", "duration", "owner_id", "description", "poster_url", "rating"]
    columns = get_movie_columns()
    update_fields = []
    params = []
    for key in allowed:
        if key in columns and key in data:
            update_fields.append(f"{key} = %s")
            params.append(data[key])

    if not update_fields:
        return jsonify({"status": "error", "message": "Nothing to update"}), 400

    params.append(movie_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"UPDATE Movie SET {', '.join(update_fields)} WHERE movie_id = %s", params
        )
        conn.commit()
        if cursor.rowcount:
            return jsonify({"status": "success", "message": "Movie updated"})
        return jsonify({"status": "error", "message": "Movie not found"}), 404
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@movies_bp.route("/admin/<int:movie_id>", methods=["DELETE"])
@require_role_decorator("admin")
def delete_movie(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Movie WHERE movie_id = %s", (movie_id,))
        conn.commit()
        if cursor.rowcount:
            return jsonify({"status": "success", "message": "Movie deleted"})
        return jsonify({"status": "error", "message": "Movie not found"}), 404
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@movies_bp.route("/<int:movie_id>/genres", methods=["GET"])
def get_genres_by_movie(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT genre FROM Movie_Genre WHERE movie_id = %s", (movie_id,))
    genre_rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": [row["genre"] for row in genre_rows]})


@movies_bp.route("/admin/<int:movie_id>/genres", methods=["POST"])
@require_role_decorator("admin")
def add_movie_genre(movie_id):
    data = request.get_json()
    genre = data.get("genre")
    if not genre:
        return jsonify({"status": "error", "message": "Genre required"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Movie_Genre (movie_id, genre) VALUES (%s, %s)",
            (movie_id, genre),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Genre added"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@movies_bp.route("/admin/<int:movie_id>/genres", methods=["DELETE"])
@require_role_decorator("admin")
def remove_movie_genre(movie_id):
    data = request.get_json()
    genre = data.get("genre")
    if not genre:
        return jsonify({"status": "error", "message": "Genre required"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM Movie_Genre WHERE movie_id = %s AND genre = %s",
            (movie_id, genre),
        )
        conn.commit()
        if cursor.rowcount:
            return jsonify({"status": "success", "message": "Genre removed"})
        return jsonify({"status": "error", "message": "Genre not found"}), 404
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@movies_bp.route("/theaters", methods=["GET"])
def get_theaters():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT theater_id, theater_name FROM Theater")
    theaters = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "data": theaters})


@movies_bp.route("/theaters", methods=["POST"])
@require_role_decorator("admin")
def create_theater():
    data = request.get_json()
    theater_id = data.get("theater_id")
    theater_name = data.get("theater_name")
    if not all([theater_id, theater_name]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Theater (theater_id, theater_name) VALUES (%s, %s)",
            (theater_id, theater_name),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Theater created"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@movies_bp.route("/admin", methods=["POST"])
@require_role_decorator("admin")
def create_movie():
    data = request.get_json()
    movie_id = data.get("movie_id")
    owner_id = data.get("owner_id")
    title = data.get("title")
    duration = data.get("duration")
    if not all([movie_id, owner_id, title, duration]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Movie (movie_id, owner_id, title, duration) VALUES (%s, %s, %s, %s)",
            (movie_id, owner_id, title, duration),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Movie created"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
