const WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS) || 60000;
const MAX = Number(process.env.RATE_LIMIT_MAX) || 60;

const hits = new Map();

function clientKey(req) {
  const forwarded = req.headers["x-forwarded-for"];
  if (typeof forwarded === "string" && forwarded.length > 0) {
    return forwarded.split(",")[0].trim();
  }
  return req.ip || "unknown";
}

function slidingWindowRateLimit(req, res, next) {
  const key = clientKey(req);
  const now = Date.now();
  const timestamps = (hits.get(key) || []).filter((t) => now - t < WINDOW_MS);

  if (timestamps.length >= MAX) {
    const retryAfterSec = Math.max(
      1,
      Math.ceil((timestamps[0] + WINDOW_MS - now) / 1000)
    );
    res.set("Retry-After", String(retryAfterSec));
    res.set("X-RateLimit-Limit", String(MAX));
    res.set("X-RateLimit-Remaining", "0");
    return res.status(429).json({
      success: false,
      message: "Too many requests",
    });
  }

  timestamps.push(now);
  hits.set(key, timestamps);
  res.set("X-RateLimit-Limit", String(MAX));
  res.set("X-RateLimit-Remaining", String(MAX - timestamps.length));
  next();
}

module.exports = slidingWindowRateLimit;
