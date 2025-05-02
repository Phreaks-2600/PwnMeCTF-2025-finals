const request = require('supertest');
const { baseUrl, adminCreds, generateRandomString } = require('./helpers');

describe('Admin: Delete any email', () => {
  const user = { email: `${generateRandomString()}@test.com`, password: generateRandomString() };
  const admin = { email: adminCreds.username, password: adminCreds.password };
  let emailId, adminToken;

  beforeAll(async () => {
    // Register and login normal user
    await request(baseUrl).post('/api/auth/register').send(user);
    const loginUser = await request(baseUrl).post('/api/auth/login').send(user);
    const userToken = loginUser.body.token;

    // Send an email
    const send = await request(baseUrl)
      .post('/api/email/send')
      .set('Authorization', `Bearer ${userToken}`)
      .send({ receiver: user.email, subject: 'To Delete', body: 'Delete me' });

    emailId = send.body._id;

    const loginAdmin = await request(baseUrl).post('/api/auth/login').send(admin);
    adminToken = loginAdmin.body.token;
  });

  it('should delete the email', async () => {
    const res = await request(baseUrl)
      .delete(`/api/admin/emails/${emailId}`)
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
    expect(res.body.message).toMatch(/deleted/i);
  });
});
