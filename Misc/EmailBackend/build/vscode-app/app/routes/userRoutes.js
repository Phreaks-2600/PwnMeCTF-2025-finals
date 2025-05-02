const express = require('express');
const { body, validationResult } = require('express-validator');
const router = express.Router();
const auth = require('../middleware/auth');
const userController = require('../controllers/userController');

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

// POST /api/user/update - Update own profile
router.post(
	'/update',
	auth,
	validate([
		body('email').isEmail().withMessage('Invalid email'),
	]),
	userController.update
);

module.exports = router;
