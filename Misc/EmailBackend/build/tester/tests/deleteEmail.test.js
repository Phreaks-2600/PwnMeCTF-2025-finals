const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('Delete Email', () => {
  const user = { email: `${generateRandomString()}@test.com`, password: generateRandomString() };
  let token = '';
  let emailId = '';

  beforeAll(async () => {
    await request(baseUrl).post('/api/auth/register').send(user);
    const login = await request(baseUrl).post('/api/auth/login').send(user);
    token = login.body.token;

    const send = await request(baseUrl)
      .post('/api/email/send')
      .set('Authorization', `Bearer ${token}`)
      .send({
        receiver: user.email,
        subject: 'To be deleted',
        body: 'This message will be deleted.'
      });

    emailId = send.body._id;
  });

  it('should delete the email', async () => {
    const res = await request(baseUrl)
      .delete(`/api/email/${emailId}`)
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
  });

  it('should not find the email in inbox', async () => {
    const res = await request(baseUrl)
      .get('/api/email')
      .set('Authorization', `Bearer ${token}`);

    const email = res.body.find(e => e._id === emailId);
    expect(email).toBeUndefined();
  });
});
