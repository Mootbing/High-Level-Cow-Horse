import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Parse a UTC datetime string from the server.
 * Server stores UTC but without 'Z' suffix, so we append it
 * to ensure JavaScript correctly interprets as UTC.
 */
export function parseUTC(dateStr: string | null | undefined): Date | null {
  if (!dateStr) return null;
  return new Date(dateStr.endsWith("Z") ? dateStr : dateStr + "Z");
}
