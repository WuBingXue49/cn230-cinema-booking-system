-- กันการ run แล้ว error เนื่องการมีการสร้าง table หรือ view นั้นๆแล้ว
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
DROP INDEX IF EXISTS idx_booking_user;
DROP INDEX IF EXISTS idx_showtime_movie; 

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
    status VARCHAR(20) NOT NULL DEFAULT 'Confirmed',
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
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

-- Payment table: เก็บข้อมูลการชำระเงินของแต่ละ booking
CREATE TABLE Payment (
    payment_id INT PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    UNIQUE (booking_id), -- แต่ละ booking จะมี payment ได้แค่ครั้งเดียว
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
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
WHERE NOT EXISTS (
    SELECT 1
    FROM Booking_Seat bs
    JOIN Booking b ON bs.booking_id = b.booking_id
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

-- ช่วยหาข้อมูลการจองของ user_id นั้นๆ ได้อย่างรวดเร็ว
CREATE INDEX idx_booking_user ON Booking(user_id);

-- ช่วยหารอบฉายของ movie_id นั้นๆ ได้อย่างรวดเร็ว
CREATE INDEX idx_showtime_movie ON Showtime(movie_id);
