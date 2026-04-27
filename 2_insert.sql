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
