USE blood_donation;

DROP PROCEDURE IF EXISTS find_donors;

DELIMITER //
CREATE PROCEDURE find_donors(IN bg VARCHAR(5), IN city_name VARCHAR(50))
BEGIN
    SELECT donor_id, name, blood_group, city, phone, last_donation
    FROM donors
    WHERE blood_group = bg 
      AND city = city_name 
      AND is_available = TRUE;
END //
DELIMITER ;