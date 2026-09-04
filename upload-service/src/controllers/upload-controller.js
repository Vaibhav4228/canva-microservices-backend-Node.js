const { uploadMediaToCloudinary, uploadUrlToCloudinary } = require("../utils/cloudinary");
const Media = require("../models/media");

function mediaSource(value) {
  return value === "ai" ? "ai" : "upload";
}

function toMediaPayload(userId, name, result, source) {
  return {
    userId,
    name,
    cloudinaryId: result.public_id,
    url: result.secure_url,
    mimeType: result.format ? `image/${result.format}` : "image/jpeg",
    size: result.bytes,
    width: result.width,
    height: result.height,
    source,
  };
}

const uploadMedia = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: "No File Found!" });
    }

    const { originalname, mimetype, size, width, height } = req.file;
    const { userId } = req.user;
    const source = mediaSource(req.body?.source);
    const cloudinaryResult = await uploadMediaToCloudinary(req.file);

    const newlyCreatedMedia = new Media({
      userId,
      name: originalname,
      cloudinaryId: cloudinaryResult.public_id,
      url: cloudinaryResult.secure_url,
      mimeType: mimetype,
      size,
      width,
      height,
      source,
    });

    await newlyCreatedMedia.save();
    res.status(201).json({ success: true, data: newlyCreatedMedia });
  } catch (e) {
    console.error("Upload error:", e.message);
    res.status(500).json({ success: false, message: e.message || "Error creating asset" });
  }
};

const saveMediaFromUrl = async (req, res) => {
  try {
    const url = String(req.body?.url || "").trim();
    if (!url) {
      return res.status(400).json({ success: false, message: "url is required" });
    }
    const allowed =
      url.startsWith("http://") || url.startsWith("https://") || url.startsWith("data:");
    if (!allowed) {
      return res.status(400).json({ success: false, message: "url must be http(s) or a data URI" });
    }

    const source = mediaSource(req.body?.source);
    const name = String(req.body?.name || (source === "ai" ? "AI generation" : "Upload")).slice(0, 200);
    const folder = source === "ai" ? "canva-ai" : "canva-uploads";
    const result = await uploadUrlToCloudinary(url, folder);
    const newlyCreatedMedia = await Media.create(
      toMediaPayload(req.user.userId, name, result, source)
    );

    res.status(201).json({ success: true, data: newlyCreatedMedia });
  } catch (e) {
    console.error("Save from url error:", e.message);
    res.status(500).json({ success: false, message: e.message || "Error saving image" });
  }
};

const getAllMediasByUser = async (req, res) => {
  try {
    const medias = await Media.find({ userId: req.user.userId }).sort({
      createdAt: -1,
    });
    res.status(200).json({ success: true, data: medias });
  } catch (e) {
    res.status(500).json({ success: false, message: "Failed to fetch assets" });
  }
};

module.exports = { uploadMedia, saveMediaFromUrl, getAllMediasByUser };
