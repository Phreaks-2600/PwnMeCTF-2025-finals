const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('Security: MongoDB Injection via /api/email/:id', () => {
  const user = {
    email: generateRandomString() + '@test.com',
    password: generateRandomString()
  };

  let token = '';

  beforeAll(async () => {
    await request(baseUrl).post('/api/auth/register').send(user);
    const login = await request(baseUrl).post('/api/auth/login').send(user);
    token = login.body.token;

    // Send one email so there's at least one in the DB
    await request(baseUrl)
      .post('/api/email/send')
      .set('Authorization', `Bearer ${token}`)
      .send({
        receiver: user.email,
        subject: 'Secret Stuff',
        body: 'pls do not leak'
      });
  });

  it('should block MongoDB query injection via path param', async () => {
    const payload = encodeURIComponent(JSON.stringify({ receiver: { $ne: null } }));

    const res = await request(baseUrl)
      .get(`/api/email/${payload}`)
      .set('Authorization', `Bearer ${token}`);

    // If the query injection worked, status is 200 and we get someone else's email.
    // If it's patched, it should reject with 400 or 403.
    expect(res.status).toBeGreaterThanOrEqual(400); // ✅ PATCHED if rejected
  });
});
