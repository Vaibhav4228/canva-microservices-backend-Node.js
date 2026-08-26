require("dotenv").config();
const express = require("express");
const proxy = require("express-http-proxy");
const cors = require("cors");
const helmet = require("helmet");
const authMiddleware = require("./middleware/auth-middleware");
const slidingWindowRateLimit = require("./middleware/rate-limit");
const log = require("./utils/log");
const {
  createProxyBreaker,
  withCircuit,
  createDemoBreaker,
} = require("./utils/circuit-breaker");

const app = express();
const PORT = process.env.PORT || 5000;
const SERVICE = "api-gateway";

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get("/health", (req, res) => {
  res.status(200).json({
    ok: true,
    service: SERVICE,
    port: PORT,
  });
});

async function pingReady(baseUrl) {
  if (!baseUrl) return false;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 2000);
  try {
    const res = await fetch(`${baseUrl}/ready`, { signal: ctrl.signal });
    return res.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

app.get("/ready", async (req, res) => {
  const checks = {
    design: await pingReady(process.env.DESIGN),
    upload: await pingReady(process.env.UPLOAD),
    subscription: await pingReady(process.env.SUBSCRIPTION),
  };
  const ready = Object.values(checks).every(Boolean);
  res.status(ready ? 200 : 503).json({
    ready,
    service: SERVICE,
    checks,
  });
});

const demoBreaker = createDemoBreaker(
  process.env.CIRCUIT_BREAKER_DEMO_URL || "http://127.0.0.1:5999/ready"
);

app.get("/breaker-demo", async (req, res) => {
  try {
    await demoBreaker.fire();
    res.status(200).json({ success: true, circuit: "closed" });
  } catch (e) {
    res.status(503).json({
      success: false,
      message: demoBreaker.opened ? "Circuit open" : "Call failed",
      circuit: demoBreaker.opened ? "open" : "closed",
      error: e.message,
    });
  }
});

app.use("/v1", slidingWindowRateLimit);

const proxyOptions = {
  proxyReqPathResolver: (req) => {
    return req.originalUrl.replace(/^\/v1/, "/api");
  },
};

function proxyTo(target, extra = {}) {
  return proxy(target, {
    ...proxyOptions,
    ...extra,
    proxyErrorHandler: (err, res) => {
      log(SERVICE, "proxy_failed", { target, error: err.message });
      res.status(502).json({
        success: false,
        message: "Service unavailable",
        target,
        error: err.message,
      });
    },
  });
}

const designBreaker = createProxyBreaker("design");

app.use(
  "/v1/designs",
  authMiddleware,
  withCircuit(designBreaker, proxyTo(process.env.DESIGN))
);

app.use(
  "/v1/media/upload",
  authMiddleware,
  proxyTo(process.env.UPLOAD, { parseReqBody: false })
);

app.use("/v1/media", authMiddleware, proxyTo(process.env.UPLOAD, { parseReqBody: true }));

app.use("/v1/subscription", authMiddleware, proxyTo(process.env.SUBSCRIPTION));

app.listen(PORT, () => {
  log(SERVICE, "listening", {
    port: PORT,
    design: process.env.DESIGN,
    upload: process.env.UPLOAD,
    subscription: process.env.SUBSCRIPTION,
  });
});
