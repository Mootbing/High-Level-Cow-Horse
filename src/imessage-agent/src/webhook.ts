import axios, { type AxiosError } from "axios";
import { config } from "./config.js";

interface WebhookPayload {
  phone_number: string;
  message_text: string;
  chat_guid: string;
  message_guid: string;
  timestamp: number;
}

interface WebhookResponse {
  reply_text: string;
  status: string;
}

const client = axios.create({
  baseURL: config.webhookUrl.replace(/\/incoming$/, ""),
  timeout: 180_000, // 3 minutes — Claude tool calls can take time
  headers: {
    "Content-Type": "application/json",
    "X-Webhook-Secret": config.webhookSecret,
  },
});

/**
 * Forward an incoming /clarmi message to the Python backend.
 * Returns the reply text to send back via iMessage.
 */
export async function forwardToBackend(
  payload: WebhookPayload
): Promise<string> {
  try {
    const response = await client.post<WebhookResponse>("/incoming", payload);
    return response.data.reply_text;
  } catch (error) {
    const axiosErr = error as AxiosError<{ detail?: string }>;

    if (axiosErr.response) {
      const status = axiosErr.response.status;
      const detail = axiosErr.response.data?.detail || axiosErr.message;
      console.error(`Webhook error (${status}): ${detail}`);

      if (status === 403) {
        return "Authentication error. Please contact Clarmi support.";
      }
      if (status === 500) {
        return "Something went wrong on our end. Please try again in a moment.";
      }
    } else if (axiosErr.code === "ECONNREFUSED") {
      console.error("Backend unavailable — connection refused");
      return "Our system is temporarily offline. Please try again shortly.";
    } else {
      console.error("Webhook request failed:", axiosErr.message);
    }

    return "Something went wrong. Please try again in a moment.";
  }
}
