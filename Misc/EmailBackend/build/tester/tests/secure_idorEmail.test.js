const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('Security: IDOR on /api/email/:id should be prevented', () => {
  const user1 = { email: generateRandomString() + '@test.com', password: generateRandomString() };
  const user2 = { email: generateRandomString() + '@test.com', password: generateRandomString() };

  let token1, token2, emailId;

  beforeAll(async () => {
    await request(baseUrl).post('/api/auth/register').send(user1);
    const login1 = await request(baseUrl).post('/api/auth/login').send(user1);
    token1 = login1.body.token;

    await request(baseUrl).post('/api/auth/register').send(user2);
    const login2 = await request(baseUrl).post('/api/auth/login').send(user2);
    token2 = login2.body.token;

    const email = await request(baseUrl)
      .post('/api/email/send')
      .set('Authorization', `Bearer ${token1}`)
      .send({ receiver: user1.email, subject: 'secret', body: 'top secret' });

    emailId = email.body._id;
  });

  it('should forbid user2 from reading user1\'s email', async () => {
    const res = await request(baseUrl)
      .get(`/api/email/${emailId}`)
      .set('Authorization', `Bearer ${token2}`);

    expect(res.status).toBeGreaterThanOrEqual(400); // ✅ PATCHED if forbidden
  });

  it('should forbid user2 from deleting user1\'s email', async () => {
    const res = await request(baseUrl)
      .delete(`/api/email/${emailId}`)
      .set('Authorization', `Bearer ${token2}`);

    expect(res.status).toBeGreaterThanOrEqual(400); // ✅ PATCHED if forbidden
  });
});
