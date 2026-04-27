from flask import Flask, Blueprint, request, jsonify, render_template
from db import get_db_connection
from routes.booking import booking_bp
from routes.showtime import showtime_bp
from routes.user import user_bp
from routes.movies import movies_bp

app = Flask(__name__)

app.register_blueprint(booking_bp, url_prefix='/bookings')
app.register_blueprint(showtime_bp, url_prefix='/showtimes')
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(movies_bp, url_prefix='/movies')

@app.route("/")
def home():
    print("HOME ROUTE HIT")
    return render_template("index.html")

#ระบบใช้ VIEW ใน database เพื่อคำนวณที่นั่งว่างแบบ real-time โดยไม่ต้องเขียน logic ฝั่ง backend
@app.route("/book", methods=["POST"])
def book():
    data = request.json

    user_id = data.get("user_id")
    showtime_id = data.get("showtime_id")
    seats = data.get("seats")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT theater_id FROM Showtime WHERE showtime_id = %s
    """, (showtime_id,))
    theater = cursor.fetchone()
    theater_id = theater["theater_id"]
    showtime_id = data.get("showtime_id")
    seats = data.get("seats")
    cursor.execute("""
        INSERT INTO Booking (user_id, showtime_id, status)
        VALUES (%s, %s, 'Confirmed')
    """, (user_id, showtime_id))

    booking_id = cursor.lastrowid

    for seat in seats:
        cursor.execute("""
        INSERT INTO Booking_Seat (booking_id, seat_number, theater_id, showtime_id)
        VALUES (%s, %s, %s, %s)
    """, (booking_id, seat, theater_id, showtime_id))

    conn.commit()

    return jsonify({
    "status": "success",
    "showtime_id": showtime_id,
    "seats": seats,
    "booking_id": booking_id
})

@app.route("/users/<int:user_id>/pending", methods=["GET"])
def get_pending(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.user_id,
               COUNT(bd.booking_id) AS total_bookings,
               COALESCE(SUM(bd.total_price), 0) AS total_pending
        FROM Users u
        LEFT JOIN Booking_Detail bd 
            ON u.user_id = bd.user_id 
            AND bd.status = 'Pending'
        WHERE u.user_id = %s
        GROUP BY u.user_id
    """, (user_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({"data": result})

if __name__ == "__main__":
    app.run(debug=True)
