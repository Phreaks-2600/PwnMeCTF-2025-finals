const { HTTPForbiddenError } = require("../utils/httpErrors");

module.exports = (req, res, next) => {
  if (!req.user?.isAdmin) {
    throw new HTTPForbiddenError("Admin access required");
  }
  next();
};
