const mongoose = require("mongoose");

const mediaSchema = new mongoose.Schema({
  userId: String,
  name: String,
  cloudinaryId: String,
  url: String,
  mimeType: String,
  size: Number,
  width: Number,
  height: Number,
  source: {
    type: String,
    enum: ["upload", "ai"],
    default: "upload",
  },
  createdAt: {
    type: Date,
    default: Date.now,
  },
});

module.exports = mongoose.models.Media || mongoose.model("Media", mediaSchema);
