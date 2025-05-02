require('dotenv').config();
const mongoose = require('mongoose');
const User = require('../models/User');
const bcrypt = require('bcrypt');

const MONGO_URI = process.env.MONGO_URI;
const ADMIN_USERNAME = process.env.ADMIN_USERNAME;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;

if (!MONGO_URI || !ADMIN_USERNAME || !ADMIN_PASSWORD) {
  console.error('Missing MONGO_URI, ADMIN_USERNAME, or ADMIN_PASSWORD in .env');
  process.exit(1);
}

const createAdmin = async () => {
  try {
    await mongoose.connect(MONGO_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true
    });

    const existing = await User.findOne({ email: ADMIN_USERNAME });
    if (existing) {
      console.log(existing);
      console.log('Admin user already exists.');
    } else {
      const hashedPassword = await bcrypt.hash(ADMIN_PASSWORD, 10);
      await User.create({
        email: ADMIN_USERNAME,
        password: hashedPassword,
        isAdmin: true
      });
      console.log('✅ Admin user created successfully.');
    }
  } catch (err) {
    console.error('❌ Failed to create admin:', err);
  } finally {
    mongoose.connection.close();
  }
};

createAdmin();
