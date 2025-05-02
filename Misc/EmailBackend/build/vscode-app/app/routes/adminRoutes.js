const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const isAdmin = require('../middleware/isAdmin');
const adminController = require('../controllers/adminController');
const { param, validationResult } = require('express-validator');

// Validation helper
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

// GET /admin/users - Get all users
router.get('/users', auth, isAdmin, adminController.getAllUsers);

// GET /admin/emails - Get all emails
router.get('/emails', auth, isAdmin, adminController.getAllEmails);

// DELETE /admin/users/:id - Delete a user
router.delete(
  '/users/:id',
  auth,
  isAdmin,
  validate([param('id').isMongoId().withMessage('Invalid user ID')]),
  adminController.deleteUser
);

// DELETE /admin/emails/:id - Delete an email
router.delete(
  '/emails/:id',
  auth,
  isAdmin,
  validate([param('id').isMongoId().withMessage('Invalid email ID')]),
  adminController.deleteEmail
);

// POST /admin/promote/:id - Promote a user to admin
router.post(
  '/promote/:id',
  auth,
  isAdmin,
  validate([param('id').isMongoId().withMessage('Invalid user ID')]),
  adminController.promoteUser
);

module.exports = router;
