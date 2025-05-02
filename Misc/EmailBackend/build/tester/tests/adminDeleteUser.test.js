const request = require('supertest');
const { baseUrl, adminCreds, generateRandomString } = require('./helpers');

describe('Admin: Delete a user', () => {
  const admin = { email: adminCreds.username, password: adminCreds.password };
  const victim = { email: `${generateRandomString()}@test.com`, password: generateRandomString() };
  let victimId, adminToken;

  beforeAll(async () => {
    // Register victim user
    await request(baseUrl).post('/api/auth/register').send(victim);
    const loginVictim = await request(baseUrl).post('/api/auth/login').send(victim);
    victimId = loginVictim.body.userId;

    const loginAdmin = await request(baseUrl).post('/api/auth/login').send(admin);
    adminToken = loginAdmin.body.token;
  });

  it('should delete the victim user', async () => {
    const res = await request(baseUrl)
      .delete(`/api/admin/users/${victimId}`)
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
    expect(res.body.message).toMatch(/deleted/i);
  });
});
