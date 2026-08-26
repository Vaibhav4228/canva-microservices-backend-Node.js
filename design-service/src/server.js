require('dotenv').config();

const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const designRoutes = require("./routes/design-routes");
const log = require("./utils/log");

const app = express();
const PORT = process.env.PORT || 5001;
const SERVICE = "design-service";

mongoose.connect(process.env.MONGO_URI).then(() => {
    log(SERVICE, "mongo_connected");
}).catch((err) => {
    log(SERVICE, "mongo_error", { error: err.message });
});


app.use(cors());
app.use(helmet());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get("/health", (req, res) => {
    res.status(200).json({
        ok: true,
        service: SERVICE,
        port: PORT,
    });
});

app.get("/ready", (req, res) => {
    const mongo = mongoose.connection.readyState === 1;
    res.status(mongo ? 200 : 503).json({
        ready: mongo,
        service: SERVICE,
        mongo,
    });
});

app.use("/api/designs", designRoutes);

async function startServer() {
    try {
        app.listen(PORT, () => {
            log(SERVICE, "listening", { port: PORT });
        });
    } catch (error) {
        console.error('Error starting server:', error);
        process.exit(1);
    }
}

startServer();