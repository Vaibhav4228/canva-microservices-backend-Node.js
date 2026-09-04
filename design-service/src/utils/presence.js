const { getRedis } = require("./redis");

function editorKey(designId, userId, tabId) {
  const tab = String(tabId || "default")
    .replace(/[^a-zA-Z0-9_-]/g, "")
    .slice(0, 64);
  return `design:${designId}:editor:${userId}:${tab || "default"}`;
}

async function listEditors(designId) {
  const redis = getRedis();
  if (!redis) return [];
  try {
    const keys = await redis.keys(`design:${designId}:editor:*`);
    if (!keys?.length) return [];
    const values = await redis.mget(...keys);
    return (values || []).filter(Boolean);
  } catch (e) {
    console.error("Presence list failed:", e.message);
    return [];
  }
}

async function heartbeat(designId, user, tabId) {
  const redis = getRedis();
  if (!redis) {
    return { editors: [], redis: false };
  }
  const payload = {
    userId: user.userId,
    name: user.name || "Editor",
    email: user.email || "",
    tabId: String(tabId || "default").slice(0, 64),
  };
  try {
    await redis.set(editorKey(designId, user.userId, tabId), payload, { ex: 30 });
    return { editors: await listEditors(designId), redis: true };
  } catch (e) {
    console.error("Presence heartbeat failed:", e.message);
    return { editors: [], redis: false, error: e.message };
  }
}

module.exports = { heartbeat, listEditors };
