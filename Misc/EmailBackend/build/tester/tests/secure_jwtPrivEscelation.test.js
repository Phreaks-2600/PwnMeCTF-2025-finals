const jwt = require('jsonwebtoken');
const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('Security: Privilege escalation via forged JWT should be rejected', () => {
  const forgedPayload = {
    id: '000000000000000000000000', // valid ObjectId format but non-existent
    email: generateRandomString() + '@fake.com',
    isAdmin: true
  };

  const token = jwt.sign(forgedPayload, process.env.JWT_SECRET, {
    algorithm: 'HS256'
  });

  it('should reject forged admin JWT for non-existent user', async () => {
    const res = await request(baseUrl)
      .get('/api/admin/users')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBeGreaterThanOrEqual(400); // ✅ PATCHED if rejected
  });

	
});
