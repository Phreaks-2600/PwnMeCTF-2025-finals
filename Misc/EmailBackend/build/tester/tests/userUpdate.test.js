const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('User update flow (secure)', () => {
  const originalEmail = `${generateRandomString()}@test.com`;
  const newEmail = `${generateRandomString()}@test.com`;
  const password = generateRandomString();
  let token = '';

  it('should register the user', async () => {
    const res = await request(baseUrl)
      .post('/api/auth/register')
      .send({ email: originalEmail, password });

    expect(res.status).toBe(200);
    expect(res.body.token).toBeDefined();
  });

  it('should login with original credentials', async () => {
    const res = await request(baseUrl)
      .post('/api/auth/login')
      .send({ email: originalEmail, password });

    expect(res.status).toBe(200);
    token = res.body.token;
  });

  it('should update the user email', async () => {
    const res = await request(baseUrl)
      .post('/api/user/update')
      .set('Authorization', `Bearer ${token}`)
      .send({ email: newEmail });

    expect(res.status).toBe(200);
  });

  it('should login with new email', async () => {
    const res = await request(baseUrl)
      .post('/api/auth/login')
      .send({ email: newEmail, password });

    expect(res.status).toBe(200);
    expect(res.body.token).toBeDefined();
  });

  it('should fail to login with old email', async () => {
    const res = await request(baseUrl)
      .post('/api/auth/login')
      .send({ email: originalEmail, password });

    expect(res.status).toBeGreaterThanOrEqual(401);
  });
});
