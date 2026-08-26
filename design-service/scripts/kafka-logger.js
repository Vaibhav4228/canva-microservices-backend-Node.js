require("dotenv").config();
const { Kafka } = require("kafkajs");
const log = require("../src/utils/log");

const brokers = (process.env.KAFKA_BROKERS || "localhost:9092").split(",");
const kafka = new Kafka({ clientId: "design-logger", brokers });
const consumer = kafka.consumer({ groupId: "design-logger" });

async function run() {
  await consumer.connect();
  await consumer.subscribe({ topic: "design.events", fromBeginning: true });
  log("kafka-logger", "listening", { topic: "design.events", brokers });
  await consumer.run({
    eachMessage: async ({ message }) => {
      const value = message.value ? message.value.toString() : "";
      log("kafka-logger", "event", { key: message.key?.toString(), value });
    },
  });
}

run().catch((e) => {
  log("kafka-logger", "failed", { error: e.message });
  process.exit(1);
});
