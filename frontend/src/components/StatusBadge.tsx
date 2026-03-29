import { Badge, type BadgeProps } from "./ui/badge";

const VARIANT_MAP: Record<string, BadgeProps["variant"]> = {
  intake: "info",
  design: "purple",
  build: "warning",
  qa: "warning",
  deployed: "success",
  cancelled: "error",
  pending: "secondary",
  in_progress: "warning",
  completed: "success",
  failed: "error",
  alive: "success",
  dead: "error",
  sent: "success",
  draft: "warning",
};

export default function StatusBadge({ status }: { status: string }) {
  const variant = VARIANT_MAP[status] || "secondary";
  return (
    <Badge variant={variant}>
      {status.replace(/_/g, " ")}
    </Badge>
  );
}
