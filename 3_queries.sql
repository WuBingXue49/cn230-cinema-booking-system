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
GROUP By showtime_id, title, theater_name;

-- ดู genre ทั้งหมดของหนังแต่ละเรื่อง
SELECT m.movie_id, m.title, STRING_AGG(mg.genre, ', ' ORDER BY mg.genre) AS genres
FROM Movie m
JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
GROUP BY m.movie_id;

-- รายได้รวมของหนังแต่ละเรื่อง
SELECT m.movie_id, m.title, SUM(cb.total_price) AS total_revenue
FROM Confirmed_Booking cb
JOIN Showtime st ON cb.showtime_id = st.showtime_id
JOIN Movie m ON st.movie_id = m.movie_id
GROUP BY m.movie_id, m.title;

-- หาหนังที่ขายดี (ฮิต) ที่สุด
SELECT m.movie_id, m.title, SUM(cb.total_price) AS total_revenue
FROM Confirmed_Booking cb
JOIN Showtime st ON cb.showtime_id = st.showtime_id
JOIN Movie m ON st.movie_id = m.movie_id
GROUP BY m.movie_id, m.title
ORDER By total_revenue DESC -- เพิ่มมาจากการหายอดขายรวม เป็นการเรียงจากมากไปน้อย 
LIMIT 1; -- เอาแค่ลำดับแรก คือที่ยอดขายมากที่สุด

/*
กรณีมีการ Cancelled ที่นั่ง 
UPDATE Booking
SET status = 'Cancelled'
WHERE booking_id = ?;

DELETE FROM Booking_Seat
WHERE booking_id = ?;
*/
