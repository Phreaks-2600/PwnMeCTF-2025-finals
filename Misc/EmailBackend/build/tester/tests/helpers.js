require('dotenv').config();

function generateRandomString(length = 24) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

module.exports = {
  baseUrl: process.env.API_BASE_URL || 'http://localhost:3000',
	adminCreds: { username: process.env.ADMIN_USERNAME, password: process.env.ADMIN_PASSWORD },
	generateRandomString: generateRandomString,
};
