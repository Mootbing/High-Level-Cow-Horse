const COLORS: Record<string, string> = {
  intake: "bg-blue-500/20 text-blue-300",
  design: "bg-purple-500/20 text-purple-300",
  build: "bg-yellow-500/20 text-yellow-300",
  qa: "bg-orange-500/20 text-orange-300",
  deployed: "bg-green-500/20 text-green-300",
  cancelled: "bg-red-500/20 text-red-300",
  pending: "bg-slate-500/20 text-slate-300",
  in_progress: "bg-yellow-500/20 text-yellow-300",
  completed: "bg-green-500/20 text-green-300",
  failed: "bg-red-500/20 text-red-300",
  alive: "bg-green-500/20 text-green-300",
  dead: "bg-red-500/20 text-red-300",
  sent: "bg-green-500/20 text-green-300",
};

export default function StatusBadge({ status }: { status: string }) {
  const color = COLORS[status] || "bg-slate-500/20 text-slate-300";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {status.replace("_", " ")}
    </span>
  );
}
