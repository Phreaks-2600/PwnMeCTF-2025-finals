const request = require('supertest');
const { baseUrl, adminCreds, generateRandomString } = require('./helpers');

describe('Admin: Promote a user', () => {
  const user = { email: `${generateRandomString()}@test.com`, password: generateRandomString() };
  const admin = { email: adminCreds.username, password: adminCreds.password };
  let userId, adminToken;

  beforeAll(async () => {
    await request(baseUrl).post('/api/auth/register').send(user);
    const loginUser = await request(baseUrl).post('/api/auth/login').send(user);
    userId = loginUser.body.userId;

    const loginAdmin = await request(baseUrl).post('/api/auth/login').send(admin);
    adminToken = loginAdmin.body.token;
  });

  it('should promote the user', async () => {
    const res = await request(baseUrl)
      .post(`/api/admin/promote/${userId}`)
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
    expect(res.body.message).toMatch(/promoted/i);
  });
});
