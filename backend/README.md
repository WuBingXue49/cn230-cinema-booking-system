# Cinema Booking System Backend

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set up MySQL database 'cinema' and run the SQL files: 1_schema.sql, 2_insert.sql
3. Run the app: `python app.py`

## API Endpoints

### User Management
- GET /users - Get all users
- GET /users/<id> - Get user by ID
- GET /users/<id>/bookings - Get booking history for user
- GET /users/no-booking - Get customers with no bookings
- POST /users - Create new user

### Showtime Management
- GET /showtimes - Get all showtimes
- GET /showtimes/<id> - Get specific showtime
- GET /showtimes/<id>/available-seats - Get available seats for showtime
- GET /movies/<title>/seats - Get showtimes and available seats by movie title
- POST /showtimes - Admin create showtime
- PUT /showtimes/<id> - Admin update showtime
- DELETE /showtimes/<id> - Admin delete showtime

### Movie Information
- GET /movies/genres - Get movie genres
- GET /movies/top - Get top selling movie
- GET /movies/revenue - Get revenue per movie
- GET /movies/admin/revenue/<movie_id> - Admin get revenue for specific movie

### Booking Management
- GET /bookings - Get all bookings
- GET /bookings/<id> - Get booking detail
- POST /bookings - Create booking (body: user_id, showtime_id, seats[])
- PUT /bookings/<id>/status - Update booking status
- PUT /bookings/<id>/cancel - Cancel booking
- PUT /bookings/<id>/use - Mark booking as Used

### Payment Management
- POST /bookings/payments - Create payment (body: booking_id)
- PUT /bookings/payments/<booking_id>/refund - Refund booking

### Staff Features
- GET /bookings/staff/<id> - Staff check booking status
- PUT /bookings/staff/<id>/status - Staff update booking status

### Legacy Endpoints (for compatibility)
- GET /showtime?title=<movie_title> - Get showtime + available seats by movie title
- GET /booking/user/<user_id> - Get bookings by user
- GET /booking/pending/<user_id> - Get pending payment summary

## Example Requests

### User Management
```bash
# Get all users
curl "http://localhost:5000/users"

# Get user by ID
curl "http://localhost:5000/users/1"

# Get booking history
curl "http://localhost:5000/users/1/bookings"

# Get customers with no bookings
curl "http://localhost:5000/users/no-booking"

# Create user
curl -X POST http://localhost:5000/users \
  -H "user_id:5" \
  -H "role:admin" \
  -H "Content-Type: application/json" \
  -d '{"user_id":6, "name":"New User", "email":"new@example.com", "password":"pass123", "role":"customer"}'
```

### Showtime Management
```bash
# Get all showtimes
curl "http://localhost:5000/showtimes"

# Get specific showtime
curl "http://localhost:5000/showtimes/1"

# Get available seats
curl "http://localhost:5000/showtimes/1/available-seats"

# Get movie seats
curl "http://localhost:5000/movies/LoveDoc/seats"

# Create showtime (Admin)
curl -X POST http://localhost:5000/showtimes \
  -H "user_id:5" \
  -H "role:admin" \
  -H "Content-Type: application/json" \
  -d '{"showtime_id":5, "movie_id":1111, "theater_id":23, "show_date":"2026-04-22 14:00:00", "price":250.00}'

# Update showtime (Admin)
curl -X PUT http://localhost:5000/showtimes/5 \
  -H "user_id:5" \
  -H "role:admin" \
  -H "Content-Type: application/json" \
  -d '{"movie_id":1111, "theater_id":23, "show_date":"2026-04-22 16:00:00", "price":300.00}'

# Delete showtime (Admin)
curl -X DELETE http://localhost:5000/showtimes/5 \
  -H "user_id:5" \
  -H "role:admin"
```

### Movie Information
```bash
# Get movie genres
curl "http://localhost:5000/movies/genres"

# Get top movie
curl "http://localhost:5000/movies/top"

# Get movie revenue
curl "http://localhost:5000/movies/revenue"

# Get revenue for specific movie (Admin)
curl "http://localhost:5000/movies/admin/revenue/1111"
```

### Booking Management
```bash
# Get all bookings
curl "http://localhost:5000/bookings"

# Get booking detail
curl "http://localhost:5000/bookings/100"

# Create booking
curl -X POST http://localhost:5000/bookings \
  -H "user_id:1" \
  -H "role:customer" \
  -H "Content-Type: application/json" \
  -d '{"user_id":1, "showtime_id":2, "seats":[1]}'

# Update booking status
curl -X PUT http://localhost:5000/bookings/100/status \
  -H "Content-Type: application/json" \
  -d '{"status":"Confirmed"}'

# Cancel booking
curl -X PUT http://localhost:5000/bookings/100/cancel \
  -H "user_id:1" \
  -H "role:customer"

# Mark as used
curl -X PUT http://localhost:5000/bookings/100/use \
  -H "user_id:4" \
  -H "role:staff"
```

### Payment Management
```bash
# Create payment
curl -X POST http://localhost:5000/bookings/payments \
  -H "user_id:1" \
  -H "role:customer" \
  -H "Content-Type: application/json" \
  -d '{"booking_id":100}'

# Refund booking
curl -X PUT http://localhost:5000/bookings/payments/100/refund \
  -H "user_id:5" \
  -H "role:admin"
```

### Staff Features
```bash
# Check booking status
curl "http://localhost:5000/bookings/staff/100" \
  -H "user_id:4" \
  -H "role:staff"

# Update booking status
curl -X PUT http://localhost:5000/bookings/staff/100/status \
  -H "user_id:4" \
  -H "role:staff" \
  -H "Content-Type: application/json" \
  -d '{"status":"Confirmed"}'
```

### Legacy Endpoints
```bash
# Get showtime by title
curl "http://localhost:5000/showtime?title=LoveDoc"

# Get bookings by user
curl "http://localhost:5000/booking/user/1"

# Get pending summary
curl "http://localhost:5000/booking/pending/2"
```