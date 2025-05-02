const User = require('../models/User');
const Email = require('../models/Email');
const { HTTPNotFoundError } = require('../utils/httpErrors');

exports.getAllUsers = async (req, res) => {
  const users = await User.find().select('-password');
  res.json(users);
};

exports.getAllEmails = async (req, res) => {
  const emails = await Email.find().sort({ timestamp: -1 });
  res.json(emails);
};

exports.deleteUser = async (req, res) => {
  const deleted = await User.findByIdAndDelete(req.params.id);
  if (!deleted) throw new HTTPNotFoundError('User not found');
  res.json({ message: 'User deleted' });
};

exports.deleteEmail = async (req, res) => {
  const deleted = await Email.findByIdAndDelete(req.params.id);
  if (!deleted) throw new HTTPNotFoundError('Email not found');
  res.json({ message: 'Email deleted' });
};

exports.promoteUser = async (req, res) => {
  const updated = await User.findByIdAndUpdate(req.params.id, { isAdmin: true });
  if (!updated) throw new HTTPNotFoundError('User not found');
  res.json({ message: 'User promoted to admin' });
};
