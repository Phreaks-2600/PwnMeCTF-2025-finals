const request = require('supertest');
const { baseUrl, adminCreds } = require('./helpers');

describe('Admin: Get all emails', () => {
  const admin = { email: adminCreds.username, password: adminCreds.password };
  let adminToken;

  beforeAll(async () => {
    const login = await request(baseUrl).post('/api/auth/login').send(admin);
    adminToken = login.body.token;
  });

  it('should return all emails', async () => {
    const res = await request(baseUrl)
      .get('/api/admin/emails')
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
  });
});
