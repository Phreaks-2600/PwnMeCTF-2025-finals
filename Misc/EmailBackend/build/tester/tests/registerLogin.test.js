const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('User Registration and Login', () => {
  const email = `${generateRandomString()}@test.com`;
  const password = generateRandomString();

  it('should register a new user', async () => {
    const res = await request(baseUrl)
      .post('/api/auth/register')
      .send({ email, password });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('token');
  });

  it('should login the user', async () => {
    const res = await request(baseUrl)
      .post('/api/auth/login')
      .send({ email, password });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('token');
  });
});
