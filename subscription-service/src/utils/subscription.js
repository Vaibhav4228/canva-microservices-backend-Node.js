const Subscription = require("../models/subscription");

const FREE_AI_LIMIT = Number(process.env.FREE_AI_LIMIT || 5);
const PREMIUM_AI_LIMIT = Number(process.env.PREMIUM_AI_LIMIT || 200);

function startOfMonth(date = new Date()) {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
}

function refreshPeriod(subscription) {
  const start = startOfMonth();
  if (!subscription.usagePeriodStart || subscription.usagePeriodStart < start) {
    subscription.usagePeriodStart = start;
    subscription.aiUsed = 0;
  }
}

function aiLimit(isPremium) {
  return isPremium ? PREMIUM_AI_LIMIT : FREE_AI_LIMIT;
}

function toPublic(subscription) {
  refreshPeriod(subscription);
  const limit = aiLimit(subscription.isPremium);
  const remaining = limit < 0 ? null : Math.max(0, limit - subscription.aiUsed);
  return {
    isPremium: subscription.isPremium,
    premiumSince: subscription.premiumSince,
    paymentProvider: subscription.paymentProvider || null,
    aiUsed: subscription.aiUsed || 0,
    aiLimit: limit,
    aiRemaining: remaining,
  };
}

async function getOrCreateSubscription(userId) {
  let subscription = await Subscription.findOne({ userId });
  if (!subscription) {
    subscription = new Subscription({ userId });
  }
  refreshPeriod(subscription);
  return subscription;
}

async function activatePremium(userId, paymentId, paymentProvider) {
  const subscription = await getOrCreateSubscription(userId);
  subscription.isPremium = true;
  subscription.premiumSince = subscription.premiumSince || new Date();
  subscription.paymentId = paymentId;
  subscription.paymentProvider = paymentProvider;
  await subscription.save();
  return subscription;
}

module.exports = {
  FREE_AI_LIMIT,
  PREMIUM_AI_LIMIT,
  getOrCreateSubscription,
  toPublic,
  activatePremium,
  aiLimit,
};
