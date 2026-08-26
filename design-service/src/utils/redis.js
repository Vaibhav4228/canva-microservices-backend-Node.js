const { Redis } = require("@upstash/redis");

let client;

function getRedis() {
  if (client !== undefined) return client;
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) {
    client = null;
    return client;
  }
  client = new Redis({ url, token });
  return client;
}

function designsKey(userId) {
  return `designs:user:${userId}`;
}

async function getCachedDesigns(userId) {
  const redis = getRedis();
  if (!redis) return null;
  try {
    return await redis.get(designsKey(userId));
  } catch (e) {
    console.error("Redis get failed:", e.message);
    return null;
  }
}

async function setCachedDesigns(userId, designs) {
  const redis = getRedis();
  if (!redis) return;
  try {
    await redis.set(designsKey(userId), designs, { ex: 30 });
  } catch (e) {
    console.error("Redis set failed:", e.message);
  }
}

async function invalidateDesignsCache(userId) {
  const redis = getRedis();
  if (!redis) return;
  try {
    await redis.del(designsKey(userId));
  } catch (e) {
    console.error("Redis del failed:", e.message);
  }
}

module.exports = {
  getCachedDesigns,
  setCachedDesigns,
  invalidateDesignsCache,
};
