USE blood_donation;

-- Clear existing data first
DELETE FROM donors;

-- Insert sample donors
INSERT INTO donors (name, blood_group, city, phone, last_donation) VALUES
('Rahul Sharma',   'A+',  'Delhi',   '9876543210', '2024-01-10'),
('Priya Singh',    'B+',  'Mumbai',  '9123456780', '2024-06-01'),
('Amit Kumar',     'O+',  'Delhi',   '9988776655', '2024-03-15'),
('Shreya Singhal', 'O+',  'Siliguri','9832145011', '2024-07-14'),
('Meena Rao',      'AB+', 'Chennai', '9765432100', '2024-08-20'),
('Vikram Das',     'B-',  'Kolkata', '9654321098', '2024-02-28'),
('Anjali Mehta',   'A-',  'Delhi',   '9543210987', '2024-05-10'),
('Rohit Verma',    'O-',  'Mumbai',  '9432109876', '2024-04-15');