const request = require('supertest');
const { baseUrl } = require('./helpers');

describe('Security: JWT none algorithm', () => {
  it('should not accept a token signed with "none"', async () => {
    const payload = { id: '123', email: 'hacker@example.com', isAdmin: true };
    const token = [
      Buffer.from(JSON.stringify({ alg: 'none', typ: 'JWT' })).toString('base64url'),
      Buffer.from(JSON.stringify(payload)).toString('base64url'),
      '' // no signature
    ].join('.');

    const res = await request(baseUrl)
      .get('/api/admin/users')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBeGreaterThanOrEqual(400);
  });
});
