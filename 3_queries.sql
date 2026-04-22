-- เช็คยอดค้างชำระของ user_id ของ customer ที่ค้นหา
SELECT u.user_id, COUNT(bd.booking_id) AS total_bookings, COALESCE(SUM(bd.total_price), 0) AS total_pending
FROM Users u
LEFT JOIN Booking_Detail bd 
    ON u.user_id = bd.user_id 
    AND bd.status = 'Pending'
    WHERE u.role = 'customer'
    	and u.user_id = 2 -- สามารถลบออกเพื่อใช้ในการดูยอดค้างของ user ที่เป็น customer ทุกคนได้
GROUP BY u.user_id;

-- เช็คเลขที่นั่งที่ว่างในแต่ละรอบฉายของชื่อหนังที่ค้นหา
/*
MySQL => GROUP_CONCAT(seat_number ORDER BY seat_number SEPARATOR ', ')
PostgreSQL / SQL Server => STRING_AGG(seat_number, ', ' ORDER BY seat_number)
*/
SELECT showtime_id, title, theater_name, show_date, price, STRING_AGG(seat_number, ', ' ORDER BY seat_number) AS seats
FROM Showtime_Detail
WHERE title = 'LoveDoc'
GROUP By showtime_id, title, theater_name , show_date, price; 

-- ดู genre ทั้งหมดของหนังแต่ละเรื่อง
SELECT m.movie_id, m.title, STRING_AGG(mg.genre, ', ' ORDER BY mg.genre) AS genres
FROM Movie m
JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
GROUP BY m.movie_id , m.title;

-- รายได้รวมของหนังแต่ละเรื่อง
SELECT m.movie_id, m.title, SUM(cb.total_price) AS total_revenue
FROM Payment p
JOIN Booking b ON p.booking_id = b.booking_id
JOIN Showtime st ON b.showtime_id = st.showtime_id
JOIN Movie m ON st.movie_id = m.movie_id
WHERE p.status = 'Confirmed'
GROUP BY m.movie_id, m.title
ORDER BY total_revenue DESC; -- เรียงจากยอดขายมากไปน้อย เพื่อให้เห็นว่าหนังเรื่องไหนขายดีสุด 

-- หาหนังที่ขายดี (ฮิต) ที่สุด
SELECT m.movie_id, m.title, SUM(cb.total_price) AS total_revenue
FROM Payment p
JOIN Booking b ON p.booking_id = b.booking_id
JOIN Showtime st ON b.showtime_id = st.showtime_id
JOIN Movie m ON st.movie_id = m.movie_id
WHERE p.status = 'Confirmed'
GROUP BY m.movie_id, m.title
ORDER By total_revenue DESC -- เพิ่มมาจากการหายอดขายรวม เป็นการเรียงจากมากไปน้อย 
LIMIT 1; -- เอาแค่ลำดับแรก คือที่ยอดขายมากที่สุด

-- อัพเดตยอดรวมของการจองแต่ละ booking_id โดยคูณราคาต่อที่นั่งกับจำนวนที่นั่งที่จอง
SELECT b.booking_id,
       COUNT(bs.seat_number) * st.price AS total_price
FROM Booking b
JOIN Booking_Seat bs ON b.booking_id = bs.booking_id
JOIN Showtime st ON b.showtime_id = st.showtime_id
GROUP BY b.booking_id, st.price;

-- กรณีมีการ Cancelled ที่นั่ง 
UPDATE Booking
SET status = 'Cancelled'
WHERE booking_id = ?;

--customer booking history
SELECT b.booking_id, m.title, t.theater_name, st.show_date, st.price
FROM Booking b
JOIN Showtime st ON b.showtime_id = st.showtime_id
JOIN Movie m ON st.movie_id = m.movie_id
JOIN Theater t ON st.theater_id = t.theater_id
WHERE b.user_id = ?

-- แสดงข้อมูลการจองทั้งหมดของ user_id = ใดก็ได้ โดยเรียงจากรอบฉายล่าสุดไปเก่าสุด และแสดงสถานะการจองด้วย
SELECT u.name, m.title, st.show_date, b.status
FROM Users u
JOIN Booking b ON u.user_id = b.user_id
JOIN Showtime st ON b.showtime_id = st.showtime_id
JOIN Movie m ON st.movie_id = m.movie_id
WHERE u.user_id = ?
ORDER BY st.show_date DESC;

-- ลูกค้าที่ไม่เคยจองหนังเลย เอาไว้ทำ marketing
SELECT u.user_id, u.name
FROM Users u
LEFT JOIN Booking b ON u.user_id = b.user_id
WHERE b.booking_id IS NULL
AND u.role = 'customer';

-- ให้ admin เพิ่มรอบฉายใหม่ของหนัง ใช้ตอนที่อยากเพิ่มรอบฉายใหม่ของหนังเรื่องเดิม หรือหนังเรื่องใหม่เลยก็ได้
INSERT INTO Showtime (showtime_id, movie_id, theater_id, show_date, price) VALUES (?, ?, ?, ?, ?);

-- admin อัพเดตข้อมูลรอบฉาย ใช้ตอนที่อยากเปลี่ยนหนัง รอบฉาย หรือราคา
UPDATE Showtime
SET movie_id = ?, theater_id = ?, show_date = ?, price = ?
WHERE showtime_id = ?; 

-- admin ลบรอบฉาย ใช้ตอนที่อยากลบรอบฉายออกไปเลย
DELETE FROM Showtime
WHERE showtime_id = ?;

-- staff(พนักงานหน้าโรงหนัง) ตรวจสอบสถานะการจองของ booking_id ใดก็ได้ เพื่อเช็คว่าการจองนั้น Confirmed, Pending หรือ Cancelled
SELECT b.booking_id, u.name, m.title, st.show_date, b.status
FROM Booking b
JOIN Users u ON b.user_id = u.user_id
JOIN Showtime st ON b.showtime_id = st.showtime_id
JOIN Movie m ON st.movie_id = m.movie_id
WHERE b.booking_id = ?;

-- staff(พนักงานหน้าโรงหนัง) อัพเดตสถานะการจองของ booking_id ใดก็ได้ เพื่อเปลี่ยนสถานะการจองเป็น Confirmed, Pending หรือ Cancelled ให้ลูกค้าได้
--(เช่น ลูกค้ามาจ่ายเงินที่หน้าโรงหนัง พนักงานก็อัพเดตสถานะการจองจาก Pending เป็น Confirmed ให้ลูกค้าได้ หรือถ้าลูกค้ามาขอคืนเงิน พนักงานก็อัพเดตสถานะการจองจาก Confirmed เป็น Cancelled ให้ลูกค้าได้)
UPDATE Booking
SET status = ?
WHERE booking_id = ?;

-- staff(พนักงานหน้าโรงหนัง) คืนเงินให้ลูกค้าในกรณีที่ลูกค้ามาขอคืนเงิน โดยการอัพเดตสถานะการชำระเงินในตาราง Payment เป็น Refunded และอัพเดตสถานะการจองในตาราง Booking เป็น Cancelled
-- ในกรณีที่มีการยกเลิกการจองหนัง ต้องอัพเดตรายได้รวมของหนังด้วยไหม?? 
UPDATE Payment
SET status = 'Refunded'
WHERE booking_id = ?;

UPDATE Booking
SET status = 'Cancelled'
WHERE booking_id = ?;

-- admin ดูรายได้รวมของหนังหนึ่งเรื่อง
SELECT m.movie_id, m.title, SUM(p.amount) AS total_revenue
FROM Payment p
JOIN Booking b ON p.booking_id = b.booking_id
JOIN Showtime st ON b.showtime_id = st.showtime_id
JOIN Movie m ON st.movie_id = m.movie_id
WHERE m.movie_id = ?
GROUP BY m.movie_id, m.title;

-- เพิ่ม status : used เพื่อเช็คว่าลูกค้าได้ใช้สิทธิ์ดูหนังในรอบฉายนี้ไปแล้วหรือยัง ถ้ายังไม่ใช้สิทธิ์ก็จะเป็น 'Confirmed' แต่ถ้าใช้สิทธิ์ดูหนังไปแล้วก็จะเปลี่ยนเป็น 'Used' เพื่อให้พนักงานหน้าโรงหนังเช็คได้ว่าลูกค้าคนนี้ได้ดูหนังในรอบฉายนี้ไปแล้ว
UPDATE Booking
SET status = 'Used'
WHERE booking_id = ?;