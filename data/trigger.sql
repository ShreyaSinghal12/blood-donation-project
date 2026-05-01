DELIMITER $$

CREATE TRIGGER before_insert_donor
BEFORE INSERT ON donors
FOR EACH ROW
BEGIN
    IF NEW.last_donation IS NOT NULL 
       AND DATEDIFF(CURDATE(), NEW.last_donation) < 90 THEN
        SET NEW.availability = 'Unavailable';
    ELSE
        SET NEW.availability = 'Available';
    END IF;
END$$

DELIMITER ;