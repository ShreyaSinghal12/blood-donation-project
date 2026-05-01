USE blood_donation;

-- View all donors
SELECT * FROM donors;

-- Test the stored procedure
CALL find_donors('O+', 'Delhi');

-- View all emergency requests
SELECT * FROM requests;

-- Check which donors are unavailable
SELECT name, blood_group, city, last_donation, is_available 
FROM donors 
WHERE is_available = FALSE;

-- Count donors by blood group
SELECT blood_group, COUNT(*) AS total_donors
FROM donors
GROUP BY blood_group
ORDER BY total_donors DESC;