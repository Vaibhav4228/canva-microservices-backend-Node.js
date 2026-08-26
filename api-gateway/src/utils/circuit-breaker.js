const CircuitBreaker = require("opossum");
const log = require("./log");

function breakerOptions() {
  return {
    timeout: Number(process.env.CIRCUIT_BREAKER_TIMEOUT_MS || 2000),
    errorThresholdPercentage: Number(process.env.CIRCUIT_BREAKER_ERROR_THRESHOLD || 50),
    resetTimeout: Number(process.env.CIRCUIT_BREAKER_RESET_MS || 10000),
    volumeThreshold: Number(process.env.CIRCUIT_BREAKER_VOLUME || 4),
  };
}

function createProxyBreaker(name) {
  const breaker = new CircuitBreaker(async (ok) => {
    if (!ok) throw new Error("downstream_failed");
    return true;
  }, breakerOptions());

  breaker.on("open", () => log("api-gateway", "circuit_open", { name }));
  breaker.on("halfOpen", () => log("api-gateway", "circuit_half_open", { name }));
  breaker.on("close", () => log("api-gateway", "circuit_close", { name }));

  return breaker;
}

function withCircuit(breaker, middleware) {
  return (req, res, next) => {
    if (breaker.opened) {
      log("api-gateway", "circuit_short_circuit", { path: req.originalUrl });
      return res.status(503).json({
        success: false,
        message: "Design service busy",
        circuit: "open",
      });
    }

    res.on("finish", () => {
      breaker.fire(res.statusCode < 500).catch(() => {});
    });

    return middleware(req, res, next);
  };
}

function createDemoBreaker(deadUrl) {
  const breaker = new CircuitBreaker(
    async () => {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), breakerOptions().timeout);
      try {
        const res = await fetch(deadUrl, { signal: ctrl.signal });
        if (!res.ok) throw new Error(`status ${res.status}`);
        return true;
      } finally {
        clearTimeout(timer);
      }
    },
    breakerOptions()
  );

  breaker.on("open", () => log("api-gateway", "circuit_open", { name: "demo" }));
  breaker.on("halfOpen", () => log("api-gateway", "circuit_half_open", { name: "demo" }));
  breaker.on("close", () => log("api-gateway", "circuit_close", { name: "demo" }));

  return breaker;
}

module.exports = { createProxyBreaker, withCircuit, createDemoBreaker };
