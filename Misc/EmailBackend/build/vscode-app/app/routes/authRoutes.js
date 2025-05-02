const express = require('express');
const { body, validationResult } = require('express-validator');
const authController = require('../controllers/authController');
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

// POST /api/auth/register - Register a new user
router.post(
  '/register',
  validate([
    body('email').isEmail().withMessage('Invalid email format'),
    body('password').isLength({ min: 6 }).withMessage('Password too short'),
  ]),
  authController.register
);

// POST /api/auth/login - Login a user
router.post(
  '/login',
  validate([
    body('email').isEmail().withMessage('Invalid email format'),
    body('password').notEmpty().withMessage('Password is required'),
  ]),
  authController.login
);

// POST /api/auth/refresh - Refresh the JWT token
router.post(
  '/refresh',
  auth,
  authController.refresh
);

module.exports = router;
