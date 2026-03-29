/**
 * ClawdBot — WhatsApp personal account bridge for OpenClaw.
 *
 * Connects to WhatsApp Web via QR code (Baileys), listens for messages
 * from the owner's phone, and forwards them to the CEO agent via Redis.
 * Agent replies come back through Redis Pub/Sub and are sent as WhatsApp replies.
 */

import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  makeCacheableSignalKeyStore,
} from "@whiskeysockets/baileys";
import { Boom } from "@hapi/boom";
import pino from "pino";
import qrcode from "qrcode-terminal";
import Redis from "ioredis";
import crypto from "crypto";

// --- Config ---
const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379/0";
const OWNER_JID = process.env.OWNER_JID || ""; // e.g., "12125551234@s.whatsapp.net" — set after first connection
const AUTH_DIR = process.env.AUTH_DIR || "./auth_state";
const CEO_STREAM = "stream:agent:ceo";
const REPLY_CHANNEL = "clawdbot:replies";

const logger = pino({ level: "warn" });

// --- Redis ---
const redis = new Redis(REDIS_URL);
const sub = new Redis(REDIS_URL);

async function publishToCEO(content) {
  const id = crypto.randomUUID().replace(/-/g, "");
  const message = {
    id,
    type: "dashboard_message", // reuse dashboard path — CEO handles it the same way
    content,
    reply_channel: "clawdbot",
  };
  await redis.xadd(
    CEO_STREAM,
    "*",
    "id",
    id,
    "data",
    JSON.stringify(message),
    "timestamp",
    new Date().toISOString()
  );
  console.log(`[clawdbot] Queued message to CEO: ${content.slice(0, 50)}...`);
}

// --- WhatsApp ---
let sock;

async function startBot() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  sock = makeWASocket({
    auth: {
      creds: state.creds,
      keys: makeCacheableSignalKeyStore(state.keys, logger),
    },
    printQRInTerminal: false,
    logger,
  });

  // QR code display
  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log("\n[clawdbot] Scan this QR code with WhatsApp:\n");
      qrcode.generate(qr, { small: true });
      console.log("");
    }

    if (connection === "open") {
      console.log("[clawdbot] Connected to WhatsApp!");
      const myJid = sock.user?.id;
      console.log(`[clawdbot] Bot JID: ${myJid}`);
      if (!OWNER_JID) {
        console.log(
          "[clawdbot] OWNER_JID not set — will forward messages from all contacts."
        );
        console.log(
          '[clawdbot] Set OWNER_JID to your number like "12125551234@s.whatsapp.net" to filter.'
        );
      }
    }

    if (connection === "close") {
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      if (reason === DisconnectReason.loggedOut) {
        console.log("[clawdbot] Logged out. Delete auth_state/ and restart.");
        process.exit(1);
      } else {
        console.log(
          `[clawdbot] Disconnected (reason: ${reason}). Reconnecting...`
        );
        startBot();
      }
    }
  });

  sock.ev.on("creds.update", saveCreds);

  // Listen for incoming messages
  sock.ev.on("messages.upsert", async ({ messages }) => {
    for (const msg of messages) {
      // Skip status broadcasts and our own messages
      if (msg.key.remoteJid === "status@broadcast") continue;
      if (msg.key.fromMe) continue;

      // If OWNER_JID is set, only listen to the owner
      if (OWNER_JID && msg.key.remoteJid !== OWNER_JID) {
        console.log(
          `[clawdbot] Ignored message from ${msg.key.remoteJid} (not owner)`
        );
        continue;
      }

      // Extract text content
      const text =
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        "";
      if (!text) continue;

      console.log(
        `[clawdbot] Message from ${msg.key.remoteJid}: ${text.slice(0, 80)}`
      );

      // Forward to CEO agent
      await publishToCEO(text);
    }
  });

  // Listen for CEO replies via Redis Pub/Sub
  await sub.subscribe(REPLY_CHANNEL);
  sub.on("message", async (channel, data) => {
    if (channel !== REPLY_CHANNEL) return;
    try {
      const parsed = JSON.parse(data);
      const replyText = parsed.content || "";
      if (!replyText) return;

      // Send reply to owner (or last sender)
      const targetJid = OWNER_JID || sock.user?.id;
      if (targetJid) {
        await sock.sendMessage(targetJid, { text: replyText });
        console.log(`[clawdbot] Sent reply: ${replyText.slice(0, 80)}...`);
      }
    } catch (err) {
      console.error("[clawdbot] Failed to parse reply:", err);
    }
  });
}

console.log("[clawdbot] Starting WhatsApp bridge...");
console.log(`[clawdbot] Redis: ${REDIS_URL}`);
startBot().catch((err) => {
  console.error("[clawdbot] Fatal:", err);
  process.exit(1);
});
