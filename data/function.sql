DELIMITER $$

CREATE FUNCTION get_available_donors(bg VARCHAR(5))
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE count_val INT;

    SELECT COUNT(*) INTO count_val
    FROM donors
    WHERE blood_group = bg AND availability = 'Available';

    RETURN count_val;
END$$

DELIMITER ;