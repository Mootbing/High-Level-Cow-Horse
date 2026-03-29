import { NavLink, useNavigate } from "react-router-dom";
import { clearToken } from "../api/client";
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
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-56 bg-background border-r border-border flex flex-col">
        <div className="p-5 border-b border-border">
          <h1 className="text-lg font-bold tracking-tight text-foreground">
            OpenClaw
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

        <div className="border-t border-border p-3">
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
    </div>
  );
}
