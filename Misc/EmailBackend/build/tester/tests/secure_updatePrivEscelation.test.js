const request = require('supertest');
const { baseUrl, generateRandomString } = require('./helpers');

describe('Security: Privilege escalation via User Arbitrary Update', () => {
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

  it('should not allow updating isAdmin of user', async () => {
    const res = await request(baseUrl)
      .post('/api/user/update')
      .set('Authorization', `Bearer ${token}`)
      .send({ email: newEmail, isAdmin: true });

		const res_login = await request(baseUrl)
			.post('/api/auth/login')
			.send({ email: newEmail, password });

		if (res_login.status === 200) {
			token = res_login.body.token;
		}
  });

  it('should not be able to call Admin routes', async () => {
		const res = await request(baseUrl)
			.get('/api/admin/emails')
			.set('Authorization', `Bearer ${token}`);

		expect(res.status).toBeGreaterThanOrEqual(400);
  });
});
