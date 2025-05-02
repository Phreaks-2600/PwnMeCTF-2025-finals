const request = require('supertest');
const { baseUrl } = require('./helpers');

describe('GET /api root', () => {
  it('should return status code 418 (I\'m a teapot)', async () => {
    const res = await request(baseUrl).get('/api');
    expect(res.status).toBe(418);
  });
});
