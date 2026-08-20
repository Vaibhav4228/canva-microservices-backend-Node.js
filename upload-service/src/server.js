require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const helmet = require("helmet");
const mediaRoutes = require("./routes/upload-routes");

const app = express();
const PORT = process.env.PORT || 5002;

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("Connected to MongoDB"))
  .catch((err) => console.error("Error connecting to MongoDB:", err));

app.use(cors());
app.use(helmet());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get("/health", (req, res) => {
  res.status(200).json({
    ok: true,
    service: "upload-service",
    port: PORT,
    mongo: mongoose.connection.readyState === 1,
  });
});

app.use("/api/media", mediaRoutes);

app.listen(PORT, () => {
  console.log(`Upload service running on port ${PORT}`);
});
