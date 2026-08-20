require("dotenv/lib/main").config();
const mongoose = require("mongoose");

async function ping() {
  const uri = process.env.MONGO_URI;
  if (!uri) {
    console.error("MONGO_URI missing");
    process.exit(1);
  }

  await mongoose.connect(uri);
  await mongoose.connection.db.admin().command({ ping: 1 });
  console.log("ok", mongoose.connection.name);
  await mongoose.disconnect();
}

ping().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
