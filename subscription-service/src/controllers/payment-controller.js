const crypto = require("crypto");
const Razorpay = require("razorpay");
const Stripe = require("stripe");
const { activatePremium, toPublic } = require("../utils/subscription");

const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:3000";
const AMOUNT = Number(process.env.PREMIUM_AMOUNT || 49900);
const CURRENCY = process.env.PREMIUM_CURRENCY || "INR";

function razorpayClient() {
  const keyId = process.env.RAZORPAY_KEY_ID;
  const keySecret = process.env.RAZORPAY_KEY_SECRET;
  if (!keyId || !keySecret) return null;
  return { client: new Razorpay({ key_id: keyId, key_secret: keySecret }), keyId, keySecret };
}

function stripeClient() {
  const secret = process.env.STRIPE_SECRET_KEY;
  if (!secret) return null;
  return new Stripe(secret);
}

exports.createOrder = async (req, res) => {
  try {
    const provider = String(req.body.provider || "").toLowerCase();
    const { userId } = req.user;

    if (provider === "razorpay") {
      const razorpay = razorpayClient();
      if (!razorpay) {
        return res.status(503).json({
          success: false,
          message: "Razorpay is not configured",
        });
      }

      const order = await razorpay.client.orders.create({
        amount: AMOUNT,
        currency: CURRENCY,
        receipt: `premium_${userId}_${Date.now()}`,
      });

      return res.status(200).json({
        success: true,
        data: {
          provider: "razorpay",
          orderId: order.id,
          amount: order.amount,
          currency: order.currency,
          keyId: razorpay.keyId,
        },
      });
    }

    if (provider === "stripe") {
      const stripe = stripeClient();
      if (!stripe) {
        return res.status(503).json({
          success: false,
          message: "Stripe is not configured",
        });
      }

      const session = await stripe.checkout.sessions.create({
        mode: "payment",
        line_items: [
          {
            quantity: 1,
            price_data: {
              currency: CURRENCY.toLowerCase(),
              unit_amount: AMOUNT,
              product_data: { name: "Canva Premium" },
            },
          },
        ],
        success_url: `${FRONTEND_URL}/subscription/success?provider=stripe&session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${FRONTEND_URL}/subscription/cancel`,
        metadata: { userId },
      });

      return res.status(200).json({
        success: true,
        data: {
          provider: "stripe",
          sessionId: session.id,
          checkoutUrl: session.url,
        },
      });
    }

    return res.status(400).json({
      success: false,
      message: "provider must be razorpay or stripe",
    });
  } catch (e) {
    console.error("Create order error:", e.message);
    res.status(500).json({
      success: false,
      message: e.message || "Error creating order",
    });
  }
};

exports.verifyPayment = async (req, res) => {
  try {
    const provider = String(req.body.provider || "").toLowerCase();
    const { userId } = req.user;

    if (provider === "razorpay") {
      const razorpay = razorpayClient();
      if (!razorpay) {
        return res.status(503).json({ success: false, message: "Razorpay is not configured" });
      }

      const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = req.body;
      const expected = crypto
        .createHmac("sha256", razorpay.keySecret)
        .update(`${razorpay_order_id}|${razorpay_payment_id}`)
        .digest("hex");

      if (expected !== razorpay_signature) {
        return res.status(400).json({ success: false, message: "Invalid Razorpay signature" });
      }

      const subscription = await activatePremium(userId, razorpay_payment_id, "razorpay");
      return res.status(200).json({ success: true, data: toPublic(subscription) });
    }

    if (provider === "stripe") {
      const stripe = stripeClient();
      if (!stripe) {
        return res.status(503).json({ success: false, message: "Stripe is not configured" });
      }

      const session = await stripe.checkout.sessions.retrieve(req.body.sessionId);
      if (session.payment_status !== "paid") {
        return res.status(400).json({ success: false, message: "Stripe payment not completed" });
      }
      if (session.metadata?.userId && session.metadata.userId !== userId) {
        return res.status(403).json({ success: false, message: "Session does not belong to this user" });
      }

      const paymentId = session.payment_intent || session.id;
      const subscription = await activatePremium(userId, String(paymentId), "stripe");
      return res.status(200).json({ success: true, data: toPublic(subscription) });
    }

    return res.status(400).json({
      success: false,
      message: "provider must be razorpay or stripe",
    });
  } catch (e) {
    console.error("Verify payment error:", e.message);
    res.status(500).json({
      success: false,
      message: e.message || "Error verifying payment",
    });
  }
};
