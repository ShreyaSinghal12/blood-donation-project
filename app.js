// ============================================================
//  BloodLink — Blood Donation & Emergency Finder
//  Stack: Node.js + Express + MySQL2
//  Run:   node app.js  →  http://localhost:5000
// ============================================================

const express = require('express');
const mysql   = require('mysql2/promise');
const path    = require('path');
const API = 'https://blood-donation-backend.onrender.com';

const app  = express();
const PORT = 5000;

// ── Middleware ───────────────────────────────────────────────
app.use(express.urlencoded({ extended: true }));
app.use(express.json());  
// Add this right after app.use(express.json())
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});  

// ── Serve static files from /public ─────────────────────────
// index.html lives at public/index.html and is served automatically at /
app.use(express.static(path.join(__dirname, 'public')));

// ── Database Pool ────────────────────────────────────────────
const pool = mysql.createPool({
    host:     process.env.MYSQLHOST     || 'localhost',
    user:     process.env.MYSQLUSER     || 'root',
    password: process.env.MYSQLPASSWORD || 'mysql123',
    database: process.env.MYSQLDATABASE || 'blood_donation',
    port:     process.env.MYSQLPORT     || 3306,
    waitForConnections: true,
    connectionLimit: 10,
});
// Verify DB connection on startup
pool.getConnection()
    .then(conn => { console.log('✅ MySQL connected'); conn.release(); })
    .catch(err  => { console.error('❌ MySQL failed:', err.message); });

// ── Helpers ──────────────────────────────────────────────────
const fmt  = v => v ? String(v).split('T')[0] : null;
const fail = (res, msg) => res.json({ status: 'error', message: msg });


// ============================================================
//  DONOR ROUTES
// ============================================================

// POST /add_donor
app.post('/add_donor', async (req, res) => {
    const { name, blood_group, city, phone, last_donation } = req.body;

    if (!name || !blood_group || !city || !phone || !last_donation)
        return fail(res, 'All fields are required.');
    if (!/^\d{10}$/.test(phone))
        return fail(res, 'Phone must be exactly 10 digits.');

    try {
        const [existing] = await pool.execute(
            'SELECT donor_id FROM donors WHERE phone = ?', [phone]
        );
        if (existing.length)
            return fail(res, 'A donor with this phone number already exists.');

        // BEFORE INSERT trigger sets is_available based on last_donation
        await pool.execute(
            `INSERT INTO donors (name, blood_group, city, phone, last_donation)
             VALUES (?, ?, ?, ?, ?)`,
            [name, blood_group, city, phone, last_donation || null]
        );
        res.json({ status: 'success', message: '✅ Donor registered successfully!' });
    } catch (err) {
        console.error('POST /add_donor:', err.message);
        fail(res, 'Database error: ' + err.message);
    }
});


// GET /search — uses stored procedure find_donors(bg, city)
app.get('/search', async (req, res) => {
    const blood_group = (req.query.blood_group || '').trim();
    const city        = (req.query.city        || '').trim();
    if (!blood_group || !city) return res.json([]);

    try {
        const [results] = await pool.query('CALL find_donors(?, ?)', [blood_group, city]);
        const rows = results[0].map(r => ({ ...r, last_donation: fmt(r.last_donation) }));
        res.json(rows);
    } catch (err) {
        console.error('GET /search:', err.message);
        res.status(500).json({ status: 'error', message: err.message });
    }
});


// GET /all_donors
app.get('/all_donors', async (req, res) => {
    try {
        const [rows] = await pool.execute('SELECT * FROM donors ORDER BY donor_id DESC');
        res.json(rows.map(r => ({ ...r, last_donation: fmt(r.last_donation) })));
    } catch (err) {
        console.error('GET /all_donors:', err.message);
        res.status(500).json({ status: 'error', message: err.message });
    }
});


// DELETE /delete_donor/:id
app.delete('/delete_donor/:id', async (req, res) => {
    try {
        await pool.execute('DELETE FROM donors WHERE donor_id = ?', [req.params.id]);
        res.json({ status: 'success', message: 'Donor deleted successfully.' });
    } catch (err) {
        console.error('DELETE /delete_donor:', err.message);
        fail(res, 'Cannot delete donor: ' + err.message);
    }
});


// ============================================================
//  EMERGENCY REQUEST ROUTES
// ============================================================

// POST /emergency
// requests table columns: patient_name, blood_group, city, phone, urgency
app.post('/emergency', async (req, res) => {
    const { patient_name, blood_group, city, phone, urgency } = req.body;

    if (!patient_name || !blood_group || !city || !phone)
        return fail(res, 'All fields are required.');
    if (!/^\d{10}$/.test(phone))
        return fail(res, 'Phone must be exactly 10 digits.');

    try {
        await pool.execute(
            `INSERT INTO requests (patient_name, blood_group, city, phone, urgency)
             VALUES (?, ?, ?, ?, ?)`,
            [patient_name, blood_group, city, phone, urgency || 'Normal']
        );
        res.json({ status: 'success', message: '🚨 Emergency request submitted! Donors will be contacted shortly.' });
    } catch (err) {
        console.error('POST /emergency:', err.message);
        fail(res, 'Database error: ' + err.message);
    }
});


// GET /all_requests
app.get('/all_requests', async (req, res) => {
    try {
        const [rows] = await pool.execute('SELECT * FROM requests ORDER BY request_id DESC');
        res.json(rows.map(r => ({ ...r, request_date: fmt(r.request_date) })));
    } catch (err) {
        console.error('GET /all_requests:', err.message);
        res.status(500).json({ status: 'error', message: err.message });
    }
});


// ============================================================
//  STATS / DASHBOARD
// ============================================================

// GET /stats
app.get('/stats', async (req, res) => {
    try {
        // is_available is BOOLEAN (1 = available, 0 = unavailable)
        const [byBloodGroup] = await pool.execute(`
            SELECT blood_group,
                   COUNT(*)              AS total,
                   SUM(is_available = 1) AS available
            FROM donors
            GROUP BY blood_group
            ORDER BY blood_group
        `);

        const [[{ total_donors }]]     = await pool.execute('SELECT COUNT(*) AS total_donors FROM donors');
        const [[{ available_donors }]] = await pool.execute('SELECT COUNT(*) AS available_donors FROM donors WHERE is_available = 1');
        const [[{ total_requests }]]   = await pool.execute('SELECT COUNT(*) AS total_requests FROM requests');

        res.json({ total_donors, available_donors, total_requests, by_blood_group: byBloodGroup });
    } catch (err) {
        console.error('GET /stats:', err.message);
        res.status(500).json({ status: 'error', message: err.message });
    }
});


// ── Start ────────────────────────────────────────────────────
app.listen(PORT, () => {
    console.log(`🚀 BloodLink running at http://localhost:${PORT}`);
});
