const User = require('../models/User');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const { generateToken } = require('../utils/jwt');
const { HTTPConflictError, HTTPUnauthorizedError } = require('../utils/httpErrors');

exports.register = async (req, res) => {
  const { email, password } = req.body;
  const existing = await User.findOne({ email });
  if (existing) throw new HTTPConflictError('User already exists');

  const hash = await bcrypt.hash(password, 10);
  const user = await User.create({ email, password: hash });
  res.json({ token: generateToken(user) });
};

exports.login = async (req, res) => {
  const { email, password } = req.body;
  const user = await User.findOne({ email });
  const valid = user && await bcrypt.compare(password, user.password);
  if (!valid) throw new HTTPUnauthorizedError('Invalid credentials');

  res.json({ token: generateToken(user), userId: user._id });
};

exports.refresh = async (req, res) => {
  const tokenVersion = req.user.tokenVersion || 0;

  const user = await User.findByIdAndUpdate(req.user.id, { tokenVersion: tokenVersion + 1 }, { new: true });
  const newToken = generateToken(user);
  res.json({ token: newToken });
};