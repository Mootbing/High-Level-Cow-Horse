/**
 * Clarmi iMessage Agent — always-on listener service.
 *
 * Uses @photon-ai/imessage-kit (free, open-source) to watch the local
 * Messages database for /clarmi-prefixed messages, forwards them to the
 * Clarmi Python backend, and sends replies back via iMessage.
 *
 * No external server needed — reads SQLite DB directly, sends via AppleScript.
 * Requires Full Disk Access permission on macOS.
 */

import { IMessageSDK, type Message } from "@photon-ai/imessage-kit";
import { config } from "./config.js";
import { normalizePhone } from "./phone-utils.js";
import { forwardToBackend } from "./webhook.js";

const COMMAND_PREFIX = "/clarmi";

const sdk = new IMessageSDK({
  debug: config.debug,
  watcher: {
    pollInterval: config.pollInterval,
    excludeOwnMessages: true,
  },
});

async function handleMessage(msg: Message): Promise<void> {
  // Skip own messages (belt + suspenders with excludeOwnMessages)
  if (msg.isFromMe) return;

  // Skip reactions
  if (msg.isReaction) return;

  const text = msg.text || "";

  // Only process /clarmi-prefixed messages
  if (!text.toLowerCase().startsWith(COMMAND_PREFIX)) return;

  const phone = normalizePhone(msg.sender);
  const preview = text.substring(COMMAND_PREFIX.length).trim().substring(0, 80);
  console.log(`[clarmi-agent] /clarmi from ${phone}: ${preview}...`);

  // Fire-and-forget: don't block the watcher's poll loop.
  // The watcher awaits handleMessage — if we await the webhook here (up to 3 min),
  // the watcher's isChecking guard blocks all subsequent polls, dropping messages.
  processAndReply(msg.sender, phone, text, msg.chatId, msg.guid, msg.date).catch(
    (err) => console.error(`[clarmi-agent] Background processing error for ${phone}:`, err)
  );
}

async function processAndReply(
  sender: string,
  phone: string,
  text: string,
  chatId: string,
  guid: string,
  date: Date,
): Promise<void> {
  const replyText = await forwardToBackend({
    phone_number: phone,
    message_text: text,
    chat_guid: chatId,
    message_guid: guid,
    timestamp: date.getTime(),
  });

  try {
    await sdk.send(sender, replyText);
    console.log(
      `[clarmi-agent] Replied to ${phone} (${replyText.length} chars)`
    );
  } catch (sendErr) {
    console.error(`[clarmi-agent] Failed to send reply to ${phone}:`, sendErr);
  }
}

async function main(): Promise<void> {
  console.log(`[clarmi-agent] Starting iMessage listener...`);
  console.log(`[clarmi-agent] Forwarding /clarmi messages to ${config.webhookUrl}`);
  console.log(`[clarmi-agent] Poll interval: ${config.pollInterval}ms`);

  await sdk.startWatching({
    onDirectMessage: handleMessage,
    onGroupMessage: handleMessage,
    onError: (error) => {
      console.error("[clarmi-agent] Watcher error:", error);
    },
  });

  console.log(`[clarmi-agent] Listening for messages...`);

  // Graceful shutdown
  const shutdown = async () => {
    console.log("\n[clarmi-agent] Shutting down...");
    await sdk.stopWatching();
    await sdk.close();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main().catch((err) => {
  console.error("[clarmi-agent] Fatal error:", err);
  process.exit(1);
});
