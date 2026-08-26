require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const helmet = require("helmet");
const subscriptionRoutes = require("./routes/subscription-routes");

const app = express();
const PORT = process.env.PORT || 5003;

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
    service: "subscription-service",
    port: PORT,
    mongo: mongoose.connection.readyState === 1,
  });
});

app.use("/api/subscription", subscriptionRoutes);

app.listen(PORT, () => {
  console.log(`Subscription service running on port ${PORT}`);
});
