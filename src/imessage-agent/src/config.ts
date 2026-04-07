import "dotenv/config";

export const config = {
  /** Clarmi backend webhook URL */
  webhookUrl:
    process.env.CLARMI_WEBHOOK_URL ||
    "http://localhost:8000/api/v1/imessage/incoming",

  /** Shared secret for webhook authentication */
  webhookSecret: process.env.IMESSAGE_WEBHOOK_SECRET || "",

  /** Watcher poll interval in ms (default: 2 seconds) */
  pollInterval: Number(process.env.POLL_INTERVAL) || 2000,

  /** Enable debug logging for the SDK */
  debug: process.env.DEBUG === "true",
};

// Validate required config
if (!config.webhookSecret) {
  console.error(
    "IMESSAGE_WEBHOOK_SECRET is required. Set it in .env or environment."
  );
  process.exit(1);
}
