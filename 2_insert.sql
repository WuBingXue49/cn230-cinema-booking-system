INSERT INTO Users VALUES (1, 'Aom', 'aom@mail.com', '1234', 'customer');
INSERT INTO Users VALUES (2, 'Boy', 'boy@gmail.com', '4567', 'customer');
INSERT INTO Users VALUES (3, 'Chai', 'chai@hotmail.com', '7890', 'customer');
INSERT INTO Users VALUES (4, 'Dan', 'dan@mail.com', '1150', 'staff');
INSERT INTO Users VALUES (5, 'Eclair', 'eclair@gmail.com', '1437', 'admin');

INSERT INTO Producer VALUES (777, 'Jenny');
INSERT INTO Producer VALUES (909, 'Kom');

INSERT INTO Movie VALUES (1111, 777, 'ForRest', 90);
INSERT INTO Movie VALUES (2222, 909, 'LoveDoc', 100);

INSERT INTO Theater VALUES (23, 'Lilly');
INSERT INTO Theater VALUES (34, 'Rose');

INSERT INTO Seat VALUES (1, 23);
INSERT INTO Seat VALUES (2, 23);
INSERT INTO Seat VALUES (3, 23);
INSERT INTO Seat VALUES (1, 34);
INSERT INTO Seat VALUES (2, 34);
INSERT INTO Seat VALUES (3, 34);

INSERT INTO Showtime VALUES (1, 1111, 23, '2026-04-20', 200);
INSERT INTO Showtime VALUES (2, 2222, 34, '2026-04-20', 150);
INSERT INTO Showtime VALUES (3, 1111, 34, '2026-04-21', 200);
INSERT INTO Showtime VALUES (4, 2222, 23, '2026-04-21', 150);

INSERT INTO Booking(booking_id, user_id, showtime_id, status, booking_date, total_price) VALUES (100, 1, 1, 'Confirmed', '2026-04-17', 400);
INSERT INTO Booking VALUES (101, 2, 2, 'Pending', '2026-04-10', 150);
INSERT INTO Booking VALUES (102, 2, 3, 'Pending', '2026-04-10', 200);
INSERT INTO Booking VALUES (103, 3, 4, 'Cancelled', '2026-04-15', 300);
INSERT INTO Booking VALUES (104, 1, 4, 'Confirmed', '2026-04-17', 150);

INSERT INTO Booking_Seat VALUES (100, 3, 23, 1);
INSERT INTO Booking_Seat VALUES (100, 2, 23, 1);
INSERT INTO Booking_Seat VALUES (101, 1, 34, 2);
INSERT INTO Booking_Seat VALUES (102, 1, 34, 3);
INSERT INTO Booking_Seat VALUES (103, 1, 23, 4);
INSERT INTO Booking_Seat VALUES (103, 2, 23, 4);
INSERT INTO Booking_Seat VALUES (104, 3, 23, 4);

INSERT INTO Movie_Genre VALUES (1111, 'Sci-Fi');
INSERT INTO Movie_Genre VALUES (1111, 'Fantasy');
INSERT INTO Movie_Genre VALUES (2222, 'Romance');

INSERT INTO Payment VALUES (1000, 100, 400, '2026-04-17', 'Confirmed');
INSERT INTO Payment VALUES (1001, 101, 150, '2026-04-10', 'Pending');
INSERT INTO Payment VALUES (1002, 102, 200, '2026-04-10', 'Pending');
INSERT INTO Payment VALUES (1003, 103, 300, '2026-04-15', 'Cancelled');
INSERT INTO Payment VALUES (1004, 104, 150, '2026-04-17', 'Confirmed');