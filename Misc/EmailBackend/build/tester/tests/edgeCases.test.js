const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('Edge Case Tests', () => {
  const user = { email: `${generateRandomString()}@test.com`, password: generateRandomString() };
  let token = '';

  beforeAll(async () => {
    await request(baseUrl).post('/api/auth/register').send(user);
    const login = await request(baseUrl).post('/api/auth/login').send(user);
    token = login.body.token;
  });

  it('should not allow registration with missing password', async () => {
    const res = await request(baseUrl)
      .post('/api/auth/register')
      .send({ email: `${generateRandomString()}@test.com` }); // Missing password

    expect(res.status).toBeGreaterThanOrEqual(400);
    expect(res.body.errors).toBeDefined();
  });

  it('should reject login with wrong password', async () => {
    const res = await request(baseUrl)
      .post('/api/auth/login')
      .send({ email: user.email, password: 'wrongpass' });

    expect(res.status).toBe(401);
    expect(res.body.error).toBeDefined();
  });

  it('should reject email send with missing fields', async () => {
    const res = await request(baseUrl)
      .post('/api/email/send')
      .set('Authorization', `Bearer ${token}`)
      .send({ receiver: '', subject: 'Oops', body: 'Missing receiver' });

    expect(res.status).toBeGreaterThanOrEqual(400);
    expect(res.body.errors).toBeDefined();
  });

  it('should not allow unauthenticated access to inbox', async () => {
    const res = await request(baseUrl)
      .get('/api/email');

    expect(res.status).toBe(401);
    expect(res.body.error || res.body.message).toBeDefined();
  });

  it('should handle deletion of non-existent email gracefully', async () => {
    const res = await request(baseUrl)
      .delete('/api/email/6123456789abcdef01234567') // Random ObjectId
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBeGreaterThanOrEqual(400);
    expect(res.body.error || res.body.message).toBeDefined();
  });

  it('should reject email with invalid email address format', async () => {
    const res = await request(baseUrl)
      .post('/api/email/send')
      .set('Authorization', `Bearer ${token}`)
      .send({ receiver: 'not-an-email', subject: 'Bad', body: 'Bad input' });

    expect(res.status).toBeGreaterThanOrEqual(400);
    expect(res.body.errors).toBeDefined();
  });
});
