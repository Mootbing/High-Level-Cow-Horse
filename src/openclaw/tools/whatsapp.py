"""WhatsApp tools exposed to agents via Claude tool_use."""

from openclaw.config import settings
from openclaw.integrations.whatsapp_client import send_text_message, send_media_message


WHATSAPP_TOOLS = [
    {
        "name": "whatsapp_send",
        "description": "Send a text message via WhatsApp to a phone number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": (
                        "Phone number in international format (e.g., +1234567890). "
                        "Use 'owner' to send to the agency owner."
                    ),
                },
                "message": {
                    "type": "string",
                    "description": "The message text to send.",
                },
            },
            "required": ["to", "message"],
        },
    },
    {
        "name": "whatsapp_send_media",
        "description": "Send an image via WhatsApp with an optional caption.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Phone number or 'owner'.",
                },
                "media_url": {
                    "type": "string",
                    "description": "Public URL of the image to send.",
                },
                "caption": {
                    "type": "string",
                    "description": "Optional caption for the image.",
                },
            },
            "required": ["to", "media_url"],
        },
    },
]


async def handle_whatsapp_tool(tool_name: str, tool_input: dict) -> dict:
    """Handle WhatsApp tool calls from agents."""
    to = tool_input.get("to", "")
    if to == "owner":
        to = settings.OWNER_PHONE

    if tool_name == "whatsapp_send":
        await send_text_message(to, tool_input["message"])
        return {"status": "sent", "to": to}
    elif tool_name == "whatsapp_send_media":
        await send_media_message(
            to, tool_input["media_url"], tool_input.get("caption", "")
        )
        return {"status": "sent", "to": to}
    return {"error": f"Unknown tool: {tool_name}"}
