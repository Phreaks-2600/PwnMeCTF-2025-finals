const Email = require('../models/Email');

exports.getInbox = async (req, res) => {
  const emails = await Email.find({ receiver: req.user.email });
  res.json(emails);
};

exports.getEmail = async (req, res) => {
  const email = await Email.findOne(JSON.parse(req.params.id));
  res.json(email);
};

exports.sendEmail = async (req, res) => {
  const { receiver, subject, body } = req.body;
  const email = await Email.create({
    sender: req.user.email,
    receiver,
    subject,
    body,
    ownerId: req.user.id
  });
  res.json(email);
};

exports.deleteEmail = async (req, res) => {
  const email = await Email.findById(req.params.id);
  await email.deleteOne();
  res.send('Deleted');
};
