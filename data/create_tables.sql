CREATE TABLE donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    blood_group ENUM('A+','A-','B+','B-','O+','O-','AB+','AB-') NOT NULL,
    city VARCHAR(100) NOT NULL,
    phone VARCHAR(10) UNIQUE NOT NULL,
    gender ENUM('Male','Female','Other') NOT NULL,
    date_of_birth DATE NOT NULL,
    last_donation DATE,
    availability VARCHAR(20) DEFAULT 'Available',

    CHECK (phone REGEXP '^[0-9]{10}$')
);
DROP TABLE requests;
CREATE TABLE requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    blood_group ENUM('A+','A-','B+','B-','O+','O-','AB+','AB-') NOT NULL,
    city VARCHAR(100) NOT NULL,
    phone VARCHAR(10) NOT NULL,
    hospital_name VARCHAR(150) NOT NULL,
    units_required INT DEFAULT 1,
    urgency ENUM('Normal','Urgent','Critical') DEFAULT 'Normal',
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
describe requests;
ALTER TABLE donors 
ADD availability ENUM('Available','Unavailable') DEFAULT 'Available';
USE blood_donation;

ALTER TABLE requests 
  MODIFY COLUMN hospital_name VARCHAR(100) DEFAULT NULL,
  MODIFY COLUMN units_required INT DEFAULT 1;