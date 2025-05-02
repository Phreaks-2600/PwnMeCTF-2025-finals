class HTTPError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
    Error.captureStackTrace(this, this.constructor);
  }
}

class HTTPBadRequestError extends HTTPError {
  constructor(message = 'Bad Request') {
    super(message, 400);
  }
}

class HTTPUnauthorizedError extends HTTPError {
  constructor(message = 'Unauthorized') {
    super(message, 401);
  }
}

class HTTPForbiddenError extends HTTPError {
  constructor(message = 'Forbidden') {
    super(message, 403);
  }
}

class HTTPNotFoundError extends HTTPError {
  constructor(message = 'Not Found') {
    super(message, 404);
  }
}

class HTTPConflictError extends HTTPError {
  constructor(message = 'Conflict') {
    super(message, 409);
  }
}

module.exports = {
  HTTPError,
  HTTPBadRequestError,
  HTTPUnauthorizedError,
  HTTPForbiddenError,
  HTTPNotFoundError,
  HTTPConflictError,
};
