const jwt = require("jsonwebtoken");
const { HTTPUnauthorizedError } = require("../utils/httpErrors");

module.exports = (req, res, next) => {
  const token = req.headers.authorization?.split(" ")[1];
  if (!token) throw new HTTPUnauthorizedError("No token provided");

  const decoded = jwt.decode(token, process.env.JWT_SECRET);

  req.user = decoded;
  next();
};