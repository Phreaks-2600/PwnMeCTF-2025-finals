const request = require('supertest');
const { baseUrl, adminCreds, generateRandomString } = require('./helpers');

describe('Admin Edge Case Tests', () => {
  const user = { email: `${generateRandomString()}@test.com`, password: generateRandomString() };
  const admin = { email: adminCreds.username, password: adminCreds.password };
  let userToken, adminToken;

  beforeAll(async () => {
    await request(baseUrl).post('/api/auth/register').send(user);
    const login = await request(baseUrl).post('/api/auth/login').send(user);
    userToken = login.body.token;

		const loginAdmin = await request(baseUrl).post('/api/auth/login').send(admin);
		adminToken = loginAdmin.body.token;
  });

  it('should forbid non-admin from accessing user list', async () => {
    const res = await request(baseUrl)
      .get('/api/admin/users')
      .set('Authorization', `Bearer ${userToken}`);

    expect(res.status).toBe(403);
    expect(res.body.error).toMatch(/admin/i);
  });

  it('should return 401 when accessing admin route without token', async () => {
    const res = await request(baseUrl).get('/api/admin/users');
    expect(res.status).toBe(401);
  });

  it('should reject promotion with invalid Mongo ID', async () => {
    const res = await request(baseUrl)
      .post('/api/admin/promote/not-a-valid-id')
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBeGreaterThanOrEqual(400);
  });

  it('should reject deleting a user with invalid Mongo ID', async () => {
    const res = await request(baseUrl)
      .delete('/api/admin/users/1234')
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBeGreaterThanOrEqual(400);
  });

  it('should reject deleting a non-existent user', async () => {
    const res = await request(baseUrl)
      .delete('/api/admin/users/6123456789abcdef01234567')
      .set('Authorization', `Bearer ${adminToken}`);

    expect([400, 404]).toContain(res.status);
  });

  it('should reject deleting a non-existent email', async () => {
    const res = await request(baseUrl)
      .delete('/api/admin/emails/6123456789abcdef01234567')
      .set('Authorization', `Bearer ${adminToken}`);

    expect([400, 404]).toContain(res.status);
  });
});
