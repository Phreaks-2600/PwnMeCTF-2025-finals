const request = require('supertest');
const jwt = require('jsonwebtoken');
const { baseUrl, generateRandomString } = require('./helpers');

describe('Security: Token refresh should work and invalidate old token', () => {
  const user = { email: generateRandomString() + '@test.com', password: 'securepass' };
  let oldToken, newToken;

  beforeAll(async () => {
    await request(baseUrl).post('/api/auth/register').send(user);
    const login = await request(baseUrl).post('/api/auth/login').send(user);
    oldToken = login.body.token;

    const refresh = await request(baseUrl)
      .post('/api/auth/refresh')
      .set('Authorization', `Bearer ${oldToken}`);

    newToken = refresh.body.token;
  });

  it('should accept the new token after refresh', async () => {
    const res = await request(baseUrl)
      .get('/api/email')
      .set('Authorization', `Bearer ${newToken}`);

    expect(res.status).toBe(200);
  });

  it('should reject the old token after refresh', async () => {
    const res = await request(baseUrl)
      .get('/api/email')
      .set('Authorization', `Bearer ${oldToken}`);

    expect(res.status).toBeGreaterThanOrEqual(401);
  });
});
