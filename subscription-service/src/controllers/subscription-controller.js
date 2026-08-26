const {
  getOrCreateSubscription,
  toPublic,
  aiLimit,
} = require("../utils/subscription");

exports.getSubscription = async (req, res) => {
  try {
    const subscription = await getOrCreateSubscription(req.user.userId);
    await subscription.save();
    return res.status(200).json({
      success: true,
      data: toPublic(subscription),
    });
  } catch (e) {
    res.status(500).json({
      success: false,
      message: e.message || "Failed to fetch subscription",
    });
  }
};

exports.consumeAiUsage = async (req, res) => {
  try {
    const subscription = await getOrCreateSubscription(req.user.userId);
    const limit = aiLimit(subscription.isPremium);
    const remaining = limit < 0 ? null : Math.max(0, limit - subscription.aiUsed);

    if (limit >= 0 && remaining === 0) {
      return res.status(403).json({
        success: false,
        message: "AI limit reached. Upgrade to premium.",
        data: toPublic(subscription),
      });
    }

    subscription.aiUsed += 1;
    await subscription.save();

    return res.status(200).json({
      success: true,
      data: toPublic(subscription),
    });
  } catch (e) {
    res.status(500).json({
      success: false,
      message: e.message || "Failed to track AI usage",
    });
  }
};
