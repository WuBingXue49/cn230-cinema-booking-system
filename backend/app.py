from flask import Flask
from routes.booking import booking_bp
from routes.showtime import showtime_bp
from routes.user import user_bp
from routes.movies import movies_bp

app = Flask(__name__)

app.register_blueprint(booking_bp, url_prefix='/booking')
app.register_blueprint(showtime_bp, url_prefix='/showtime')
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(movies_bp, url_prefix='/movies')

if __name__ == '__main__':
    app.run(debug=True)