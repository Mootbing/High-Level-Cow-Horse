import { useState, useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { clearToken, api } from "../api/client";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import {
  LayoutGrid,
  MessageSquare,
  FolderOpen,
  Cpu,
  Search,
  Mail,
  BookOpen,
  ScrollText,
  LogOut,
  ListOrdered,
  Bomb,
  Loader2,
} from "lucide-react";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutGrid },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/projects", label: "Projects", icon: FolderOpen },
  { to: "/agents", label: "Agents", icon: Cpu },
  { to: "/prospects", label: "Prospects", icon: Search },
  { to: "/emails", label: "Emails", icon: Mail },
  { to: "/knowledge", label: "Knowledge", icon: BookOpen },
  { to: "/logs", label: "Logs", icon: ScrollText },
  { to: "/queues", label: "Queues", icon: ListOrdered },
];

function NuclearModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [preview, setPreview] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [nuking, setNuking] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setLoading(true);
      setResult(null);
      api.nuclearPreview().then(setPreview).catch(() => setPreview(null)).finally(() => setLoading(false));
    }
  }, [open]);

  if (!open) return null;

  const handleNuke = async () => {
    setNuking(true);
    try {
      const res = await api.nuclearReset();
      setResult(res.status === "nuked" ? "All data destroyed." : "Something went wrong.");
    } catch {
      setResult("Nuclear reset failed.");
    } finally {
      setNuking(false);
    }
  };

  const LABELS: Record<string, string> = {
    projects: "Projects",
    tasks: "Tasks",
    agent_logs: "Agent Logs",
    prospects: "Prospects",
    emails: "Emails",
    messages: "Messages",
    knowledge: "Knowledge Entries",
    vercel_projects: "Vercel Projects",
    github_repos: "GitHub Repos",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-background border border-border rounded-lg shadow-xl w-full max-w-md mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-bold text-destructive flex items-center gap-2">
            <Bomb className="w-5 h-5" />
            Nuclear Reset
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            This will permanently delete all data, Vercel projects, and GitHub repos.
          </p>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          ) : result ? (
            <div className="text-center py-4">
              <p className="text-sm font-medium text-foreground">{result}</p>
              <Button size="sm" className="mt-4" onClick={onClose}>Close</Button>
            </div>
          ) : preview ? (
            <>
              <div className="space-y-2 mb-6">
                {Object.entries(LABELS).map(([key, label]) => {
                  const count = preview[key] ?? 0;
                  if (count === 0) return null;
                  return (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{label}</span>
                      <span className="font-mono text-destructive">{count}</span>
                    </div>
                  );
                })}
                {Object.values(preview).every((v) => v === 0) && (
                  <p className="text-sm text-muted-foreground text-center">Nothing to delete.</p>
                )}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="flex-1 bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  onClick={handleNuke}
                  disabled={nuking}
                >
                  {nuking ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Bomb className="w-4 h-4 mr-2" />}
                  {nuking ? "Nuking..." : "Confirm Nuclear"}
                </Button>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">Failed to load preview.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const [nuclearOpen, setNuclearOpen] = useState(false);

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-56 bg-background border-r border-border flex flex-col">
        <div className="p-5 border-b border-border">
          <h1 className="text-lg font-bold tracking-tight text-foreground">
            Clarmi Design Studio
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            AI Design Agency
          </p>
        </div>

        <nav className="flex-1 py-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-5 py-2.5 text-sm transition-colors",
                  isActive
                    ? "text-foreground bg-accent"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                )
              }
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-3 space-y-1">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={() => setNuclearOpen(true)}
          >
            <Bomb className="w-4 h-4 mr-2" />
            Nuclear
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-muted-foreground hover:text-foreground"
            onClick={() => {
              clearToken();
              navigate("/login");
            }}
          >
            <LogOut className="w-4 h-4 mr-2" />
            Sign out
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-background">{children}</main>

      <NuclearModal open={nuclearOpen} onClose={() => setNuclearOpen(false)} />
    </div>
  );
}
