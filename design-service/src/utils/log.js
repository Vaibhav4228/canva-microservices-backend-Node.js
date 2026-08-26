function log(service, msg, extra = {}) {
  console.log(
    JSON.stringify({
      ts: new Date().toISOString(),
      service,
      msg,
      ...extra,
    })
  );
}

module.exports = log;
