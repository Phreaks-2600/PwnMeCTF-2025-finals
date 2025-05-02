const express = require('express');
const cors = require('cors');
require('dotenv').config();

const authRoutes = require('./routes/authRoutes');
const emailRoutes = require('./routes/emailRoutes');
const userRoutes = require('./routes/userRoutes');
const adminRoutes = require('./routes/adminRoutes');

const errorHandler = require('./middleware/errorHandler');

const app = express();

app.use(cors());
app.use(express.json());

app.use('/api/auth', authRoutes);
app.use('/api/email', emailRoutes);
app.use('/api/user', userRoutes);
app.use('/api/admin', adminRoutes);
app.all('/api', (req, res) => {
	res.sendStatus(418); // I'm a teapot (keep this for the)
});

app.use(errorHandler);

module.exports = app;
