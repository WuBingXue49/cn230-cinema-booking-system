DROP DATABASE IF EXISTS cinema;
CREATE DATABASE cinema;
USE cinema;

-- กันการ run แล้ว error เนื่องการมีการสร้าง table หรือ view นั้นๆแล้ว
DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS booking_Seat;
DROP TABLE IF EXISTS Booking;
DROP TABLE IF EXISTS Seat;
DROP TABLE IF EXISTS Showtime;
DROP TABLE IF EXISTS Movie_Genre;
DROP TABLE IF EXISTS Movie;
DROP TABLE IF EXISTS Producer;
DROP TABLE IF EXISTS Theater;
DROP TABLE IF EXISTS Users;
DROP VIEW IF EXISTS Booking_Detail;
DROP VIEW IF EXISTS Available_Seats;
DROP VIEW IF EXISTS Showtime_Detail;
DROP VIEW if EXISTS Confirmed_Booking;


CREATE TABLE Producer (
    owner_id INT PRIMARY KEY,
    owner_name VARCHAR(100) NOT NULL
);

CREATE TABLE Users (
    user_id INT PRIMARY KEY ,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(10) NOT NULL
);

CREATE TABLE Theater (
    theater_id INT PRIMARY KEY,
    theater_name VARCHAR(100) NOT NULL
);

CREATE TABLE Movie (
    movie_id INT PRIMARY KEY,
    owner_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    duration INT NOT NULL,
    description VARCHAR(255),
    poster_url VARCHAR(255),
    rating DECIMAL(3,1),
    FOREIGN KEY (owner_id) REFERENCES Producer(owner_id)
);

CREATE TABLE Showtime (
    showtime_id INT PRIMARY KEY,
    movie_id INT NOT NULL,
    theater_id INT NOT NULL,
    show_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES Movie(movie_id) ON DELETE CASCADE, -- ถ้าหนังถูกลบ รอบฉายก็จะถูกลบด้วย
    FOREIGN KEY (theater_id) REFERENCES Theater(theater_id) ON DELETE CASCADE -- ถ้าโรงหนังถูกลบ รอบฉายก็จะถูกลบด้วย
);

CREATE TABLE Movie_Genre (
    movie_id INT, 
    genre VARCHAR(100) NOT NULL, 
    PRIMARY KEY (movie_id, genre), -- หนังแต่ละเรื่องสามารถมี genre ได้หลายอัน แต่ genre เดียวกันไม่ควรซ้ำในหนังเรื่องเดียวกัน
    FOREIGN KEY (movie_id) REFERENCES Movie(movie_id) ON DELETE CASCADE -- ถ้าหนังถูกลบ genre ของหนังก็จะถูกลบด้วย
);

CREATE TABLE Booking (
    booking_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    showtime_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CHECK (status IN ('Pending','Confirmed','Cancelled','Used')),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE, -- ถ้า user ถูกลบ booking ก็จะถูกลบด้วย
    FOREIGN KEY (showtime_id) REFERENCES Showtime(showtime_id) ON DELETE CASCADE -- ถ้ารอบฉายถูกลบ booking ก็จะถูกลบด้วย
);

CREATE TABLE Seat (
    seat_number VARCHAR(10) NOT NULL,
    theater_id INT NOT NULL,
    PRIMARY KEY (seat_number, theater_id),
    FOREIGN KEY (theater_id) REFERENCES Theater(theater_id) ON DELETE CASCADE
);

CREATE TABLE Booking_Seat (
    booking_id INT NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    theater_id INT NOT NULL,
    showtime_id INT NOT NULL, -- เพื่อให้รู้ว่าที่นั่งนี้จองในรอบฉายไหน จะได้เช็คได้ว่าที่นั่งนี้ว่างมั้ย
    PRIMARY KEY (booking_id, seat_number, theater_id),
    UNIQUE (seat_number, theater_id, showtime_id), -- ที่นั่งเดียวกันในโรงเดียวกัน รอบเดียวกัน จองได้แค่ครั้งเดียว
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id) ON DELETE CASCADE, -- ถ้าการจองถูกลบ ที่นั่งใน booking นั้นก็จะถูกลบด้วย
    FOREIGN KEY (seat_number, theater_id) REFERENCES Seat(seat_number, theater_id) ON DELETE CASCADE, -- ถ้าที่นั่งถูกลบ ข้อมูลการจองที่ใช้ที่นั่งนั้นก็จะถูกลบด้วย
    FOREIGN KEY (showtime_id) REFERENCES Showtime(showtime_id) ON DELETE CASCADE
);

CREATE TABLE Payment (
    payment_id INT PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('Pending','Confirmed','Refunded','Cancelled')),
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id) ON DELETE CASCADE
);

-- จะแสดงข้อมูลการจองทั้งหมดของทุก user
CREATE VIEW Booking_Detail AS
SELECT u.user_id,
       b.booking_id,
       COUNT(bs.seat_number) * st.price AS total_price,
       b.status
FROM Users u
JOIN Booking b ON u.user_id = b.user_id
JOIN Booking_Seat bs ON b.booking_id = bs.booking_id
JOIN Showtime st ON b.showtime_id = st.showtime_id
GROUP BY u.user_id, b.booking_id, b.status, st.price;

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
  		AND b.status IN ('Pending','Confirmed')
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

CREATE INDEX idx_booking_user ON Booking(user_id);
CREATE INDEX idx_showtime_movie ON Showtime(movie_id);
CREATE INDEX idx_booking_showtime ON Booking(showtime_id);
CREATE INDEX idx_payment_booking ON Payment(booking_id);

INSERT INTO Users VALUES (1, 'Aom', 'aom@mail.com', '1234', 'customer');
INSERT INTO Users VALUES (2, 'Boy', 'boy@gmail.com', '4567', 'customer');
INSERT INTO Users VALUES (3, 'Chai', 'chai@hotmail.com', '7890', 'customer');
INSERT INTO Users VALUES (4, 'Dan', 'dan@mail.com', '1150', 'staff');
INSERT INTO Users VALUES (5, 'Eclair', 'eclair@gmail.com', '1437', 'admin');

INSERT INTO Producer VALUES (777, 'Jenny');
INSERT INTO Producer VALUES (909, 'Kom');
INSERT INTO Producer VALUES (333, 'Tom');
INSERT INTO Producer VALUES (444, 'Nok');

INSERT INTO Movie VALUES (1111, 777, 'ForRest', 90, 'An emotional nature adventure about healing and family.', 'https://example.com/forrest.jpg', 8.3);
INSERT INTO Movie VALUES (2222, 909, 'LoveDoc', 100, 'A romantic comedy where a doctor falls in love with a patient.', 'https://example.com/lovedoc.jpg', 7.6);
INSERT INTO Movie VALUES (3333, 333, 'CyberRush', 115, 'A high-speed cyber-thriller set in a neon megacity.', 'https://example.com/cyberrush.jpg', 8.9);
INSERT INTO Movie VALUES (4444, 444, 'Mystery Lake', 105, 'A suspenseful drama about a missing person in a quiet town.', 'https://example.com/mysterylake.jpg', 7.8);

INSERT INTO Theater VALUES (23, 'Lilly');
INSERT INTO Theater VALUES (34, 'Rose');
INSERT INTO Theater VALUES (45, 'Orchid');

INSERT INTO Seat VALUES ('1', 23);
INSERT INTO Seat VALUES ('2', 23);
INSERT INTO Seat VALUES ('3', 23);
INSERT INTO Seat VALUES ('4', 23);
INSERT INTO Seat VALUES ('5', 23);
INSERT INTO Seat VALUES ('1', 34);
INSERT INTO Seat VALUES ('2', 34);
INSERT INTO Seat VALUES ('3', 34);
INSERT INTO Seat VALUES ('4', 34);
INSERT INTO Seat VALUES ('5', 34);
INSERT INTO Seat VALUES ('1', 45);
INSERT INTO Seat VALUES ('2', 45);
INSERT INTO Seat VALUES ('3', 45);
INSERT INTO Seat VALUES ('4', 45);
INSERT INTO Seat VALUES ('5', 45);

INSERT INTO Showtime VALUES (1, 1111, 23, '2026-04-20 13:30:00', 200);
INSERT INTO Showtime VALUES (2, 2222, 34, '2026-04-20 15:00:00', 150);
INSERT INTO Showtime VALUES (3, 1111, 34, '2026-04-21 17:30:00', 200);
INSERT INTO Showtime VALUES (4, 2222, 23, '2026-04-21 19:30:00', 150);
INSERT INTO Showtime VALUES (5, 3333, 45, '2026-04-22 14:00:00', 220);
INSERT INTO Showtime VALUES (6, 4444, 23, '2026-04-22 20:00:00', 180);
INSERT INTO Showtime VALUES (7, 3333, 23, '2026-04-23 16:00:00', 220);
INSERT INTO Showtime VALUES (8, 4444, 34, '2026-04-23 19:00:00', 180);

INSERT INTO Booking VALUES (100, 1, 1, 'Confirmed', '2026-04-17 09:00:00');
INSERT INTO Booking VALUES (101, 2, 2, 'Pending', '2026-04-10 12:15:00');
INSERT INTO Booking VALUES (102, 2, 3, 'Pending', '2026-04-10 12:40:00');
INSERT INTO Booking VALUES (103, 3, 4, 'Cancelled', '2026-04-15 18:20:00');
INSERT INTO Booking VALUES (104, 1, 4, 'Confirmed', '2026-04-17 10:00:00');
INSERT INTO Booking VALUES (105, 3, 5, 'Confirmed', '2026-04-21 08:30:00');
INSERT INTO Booking VALUES (106, 1, 6, 'Pending', '2026-04-22 09:45:00');
INSERT INTO Booking VALUES (107, 2, 7, 'Pending', '2026-04-22 10:05:00');

INSERT INTO Booking_Seat VALUES (100, '3', 23, 1);
INSERT INTO Booking_Seat VALUES (100, '2', 23, 1);
INSERT INTO Booking_Seat VALUES (101, '1', 34, 2);
INSERT INTO Booking_Seat VALUES (102, '1', 34, 3);
INSERT INTO Booking_Seat VALUES (103, '1', 23, 4);
INSERT INTO Booking_Seat VALUES (103, '2', 23, 4);
INSERT INTO Booking_Seat VALUES (104, '3', 23, 4);
INSERT INTO Booking_Seat VALUES (105, '2', 45, 5);
INSERT INTO Booking_Seat VALUES (106, '4', 23, 6);
INSERT INTO Booking_Seat VALUES (107, '5', 23, 7);

INSERT INTO Movie_Genre VALUES (1111, 'Sci-Fi');
INSERT INTO Movie_Genre VALUES (1111, 'Fantasy');
INSERT INTO Movie_Genre VALUES (2222, 'Romance');
INSERT INTO Movie_Genre VALUES (3333, 'Action');
INSERT INTO Movie_Genre VALUES (3333, 'Thriller');
INSERT INTO Movie_Genre VALUES (4444, 'Mystery');
INSERT INTO Movie_Genre VALUES (4444, 'Drama');

INSERT INTO Payment VALUES (1000, 100, 400, 'Confirmed', '2026-04-17 09:30:00');
INSERT INTO Payment VALUES (1001, 101, 150, 'Pending', '2026-04-10 12:45:00');
INSERT INTO Payment VALUES (1002, 102, 200, 'Pending', '2026-04-10 13:05:00');
INSERT INTO Payment VALUES (1003, 103, 300, 'Cancelled', '2026-04-15 18:45:00');
INSERT INTO Payment VALUES (1004, 104, 150, 'Confirmed', '2026-04-17 11:05:00');
INSERT INTO Payment VALUES (1005, 105, 220, 'Confirmed', '2026-04-21 10:30:00');
INSERT INTO Payment VALUES (1006, 106, 180, 'Pending', '2026-04-22 10:10:00');
