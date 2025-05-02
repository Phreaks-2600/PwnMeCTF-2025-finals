const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('Send and Receive Email', () => {
  const user = { email: `${generateRandomString()}@test.com`, password: generateRandomString() };
  let token = '';

  beforeAll(async () => {
    await request(baseUrl).post('/api/auth/register').send(user);
    const login = await request(baseUrl).post('/api/auth/login').send(user);
    token = login.body.token;
  });

  it('should send an email to self', async () => {
    const res = await request(baseUrl)
      .post('/api/email/send')
      .set('Authorization', `Bearer ${token}`)
      .send({
        receiver: user.email,
        subject: 'Hello!',
        body: 'This is a test message.'
      });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('receiver', user.email);
  });

  it('should receive the sent email in inbox', async () => {
    const res = await request(baseUrl)
      .get('/api/email')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.length).toBeGreaterThan(0);
  });
});
