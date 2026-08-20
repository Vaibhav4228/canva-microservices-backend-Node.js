require("dotenv").config();
const express = require("express");
const proxy = require("express-http-proxy");
const cors = require("cors");
const helmet = require("helmet");
const authMiddleware = require("./middleware/auth-middleware");
const slidingWindowRateLimit = require("./middleware/rate-limit");

const app = express();
const PORT = process.env.PORT || 5000;

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get("/health", (req, res) => {
    res.status(200).json({
        ok: true,
        service: "api-gateway",
        port: PORT,
    });
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
            console.error(`Proxy failed -> ${target}`, err.message);
            res.status(502).json({
                success: false,
                message: "Service unavailable",
                target,
                error: err.message,
            });
        },
    });
}

app.use("/v1/designs", authMiddleware, proxyTo(process.env.DESIGN));

app.use(
    "/v1/media/upload",
    authMiddleware,
    proxyTo(process.env.UPLOAD, { parseReqBody: false })
);

app.use("/v1/media", authMiddleware, proxyTo(process.env.UPLOAD, { parseReqBody: true }));

app.use("/v1/subscription", authMiddleware, proxyTo(process.env.SUBSCRIPTION));

app.listen(PORT, () => {
    console.log(`API Gateway running on ${PORT}`);
    console.log(`Proxy /v1/designs -> ${process.env.DESIGN}`);
    console.log(`Proxy /v1/media -> ${process.env.UPLOAD}`);
    console.log(`Proxy /v1/subscription -> ${process.env.SUBSCRIPTION}`);
});
