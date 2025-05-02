const mongoose = require('mongoose');

const emailSchema = new mongoose.Schema({
  sender: { type: String, required: true },
  receiver: { type: String, required: true },
  subject: String,
  body: String,
  timestamp: { type: Date, default: Date.now },
  ownerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' } // for inbox access control
});

module.exports = mongoose.model('Email', emailSchema);
