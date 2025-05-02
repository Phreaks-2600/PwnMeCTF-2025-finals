const express = require('express');
const { body, param, validationResult } = require('express-validator');
const emailController = require('../controllers/emailController');
const auth = require('../middleware/auth');

const router = express.Router();

const validate = validations => [
  ...validations,
  (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }
    next();
  },
];

// GET /api/email/inbox - Get user's inbox
router.get('/', auth, emailController.getInbox);

// GET /api/email/sent - Get user's sent emails
router.get(
  '/:id',
  auth,
  validate([
    param('id').notEmpty().withMessage('Invalid email ID format'),
  ]),
  emailController.getEmail
);

// POST /api/email/send - Send an email
router.post(
  '/send',
  auth,
  validate([
    body('receiver').isEmail().withMessage('Receiver must be a valid email'),
    body('subject').notEmpty().withMessage('Subject is required'),
    body('body').notEmpty().withMessage('Body cannot be empty'),
  ]),
  emailController.sendEmail
);

// POST /api/email/receive - Receive an email
router.delete(
  '/:id',
  auth,
  validate([
    param('id').isMongoId().withMessage('Invalid email ID format'),
  ]),
  emailController.deleteEmail
);

module.exports = router;
