const { Kafka } = require("kafkajs");
const log = require("./log");

const brokers = (process.env.KAFKA_BROKERS || "localhost:9092").split(",");
const kafka = new Kafka({ clientId: "design-service", brokers });
const producer = kafka.producer();
let connected = false;

async function emitDesignEvent(event, payload) {
  try {
    if (!connected) {
      await producer.connect();
      connected = true;
      log("design-service", "kafka_connected", { brokers });
    }
    await producer.send({
      topic: "design.events",
      messages: [
        {
          key: payload.designId,
          value: JSON.stringify({
            event,
            ...payload,
            ts: new Date().toISOString(),
          }),
        },
      ],
    });
  } catch (e) {
    log("design-service", "kafka_produce_failed", { event, error: e.message });
  }
}

module.exports = { emitDesignEvent };
