-- กันการ run แล้ว error เนื่องการมีการสร้าง table หรือ view นั้นๆแล้ว
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Booking;
DROP TABLE IF EXISTS Seat;
DROP TABLE IF EXISTS Producer;
DROP TABLE IF EXISTS Movie;
DROP TABLE IF EXISTS Movie_Genre;
DROP TABLE IF EXISTS Showtime;
DROP TABLE IF EXISTS Theater;
DROP TABLE IF EXISTS booking_Seat;
DROP VIEW IF EXISTS Booking_Detail;
DROP VIEW IF EXISTS Available_Seats;
DROP VIEW IF EXISTS Showtime_Detail;
DROP VIEW if EXISTS Confirmed_Booking;
DROP INDEX IF EXISTS idx_booking_user;
DROP INDEX IF EXISTS idx_showtime_movie;

CREATE TABLE Users (
    user_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(10) NOT NULL
);

CREATE TABLE Booking (
    booking_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    showtime_id INT NOT NULL,
    status VARCHAR(20) NOt NULL DEFAULT 'Confirmed',
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_price DECIMAL(10,2), -- แต่ละการจองไม่ได้มีที่นั่งเดียว
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE, -- ถ้า user ถูกลบ booking ก็จะถูกลบด้วย
    FOREIGN KEY (showtime_id) REFERENCES Showtime(showtime_id) ON DELETE CASCADE
);

CREATE TABLE Seat (
    seat_number VARCHAR(10) NOT NULL,
    theater_id INT NOT NULL,
    PRIMARY KEY (seat_number, theater_id),
    FOREIGN KEY (theater_id) REFERENCES Theater(theater_id)
);

CREATE TABLE Producer (
    owner_id INT PRIMARY KEY,
    owner_name VARCHAR(100) NOT NULL
);

CREATE TABLE Movie (
    movie_id INT PRIMARY KEY,
    owner_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    duration INT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES Producer(owner_id)
);

CREATE TABLE Movie_Genre (
    movie_id INT,
    genre VARCHAR(100) NOT NULL,
    PRIMARY KEY (movie_id, genre),
);

-- จะแสดงข้อมูลการจองทั้งหมดของทุก user
CREATE VIEW Booking_Detail AS 
SELECT u.user_id, b.booking_id, b.total_price, b.status
FROM Users u 
JOIN Booking b ON u.user_id = b.user_id; -- idx_booking_user ถูกเรียกเพื่อให้หาข้อมูลได้เร็วขึ้น

-- ค้นหาที่นั่งที่ว่าง
CREATE VIEW Available_Seats AS
SELECT s.seat_number, s.theater_id, st.showtime_id
FROM Seat s
JOIN Showtime st ON s.theater_id = st.theater_id -- ที่นั่งทุกตัว × ทุกรอบฉาย
WHERE NOT EXISTS ( -- คัดเอาอันที่ไม่มี booking
    SELECT 1 -- เช็คว่ามี row มั้ย
    FROM Booking_Seat bs
    JOIN Booking b ON bs.booking_id = b.booking_id -- จะได้ข้อมูลการจองในที่นั่งนี้ โรงนี้ รอบฉายนี้
    WHERE bs.seat_number = s.seat_number
  		AND bs.theater_id = s.theater_id
  		AND b.showtime_id = st.showtime_id
  		AND b.status != 'Cancelled'
);

-- แสดงข้อมูลรอบฉายของหนังแต่ละเรื่องที่มีที่นั่งว่าง
CREATE VIEW Showtime_Detail AS
SELECT st.showtime_id, m.title, t.theater_name, st.show_date, st.price, a.seat_number
FROM Showtime st
JOIN Movie m ON st.movie_id = m.movie_id -- idx_showtime_movie ถูกเรียกเพื่อให้หาข้อมูลได้เร็วขึ้น
JOIN Theater t ON st.theater_id = t.theater_id
JOIN Available_Seats a ON st.showtime_id = a.showtime_id; -- ใช้ Available_Seats เพื่อเอาข้อมูลแค่ที่นั่งว่างอยู่

-- แสดงการจองที่ Confirmed แล้ว
CREATE VIEW Confirmed_Booking AS
SELECT * FROM Booking
WHERE status = 'Confirmed';

-- ช่วยหาข้อมูลการจองของ user_id นั้นๆ ได้อย่างรวดเร็ว
CREATE INDEX idx_booking_user ON Booking(user_id);

-- ช่วยหารอบฉายของ movie_id นั้นๆ ได้อย่างรวดเร็ว
CREATE INDEX idx_showtime_movie ON Showtime(movie_id);
