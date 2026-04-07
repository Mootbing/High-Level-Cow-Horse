/**
 * Normalize a phone number for consistent matching.
 *
 * iMessage handle.address can be:
 *   - Phone: "+15555550100", "+447700900000"
 *   - Email: "user@icloud.com" (iMessage-only contacts)
 *
 * For phone numbers: strip +, spaces, dashes, parens.
 * For US numbers (11 digits starting with 1): strip the leading 1.
 * For emails: return as-is.
 */
export function normalizePhone(address: string): string {
  // If it looks like an email, pass through
  if (address.includes("@")) {
    return address.toLowerCase().trim();
  }

  let cleaned = address.replace(/[+\s\-()]/g, "");

  // US numbers: 11 digits starting with 1 → strip the 1
  if (cleaned.length === 11 && cleaned.startsWith("1")) {
    cleaned = cleaned.substring(1);
  }

  return cleaned;
}
