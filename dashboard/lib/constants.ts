import {
  BarChart3,
  BookOpen,
  Globe,
  LayoutDashboard,
  ListTodo,
  Mail,
  Map,
  MessageSquare,
  Rocket,
  Users,
} from "lucide-react";

export const STATUS_COLORS: Record<string, string> = {
  intake: "#8e8e93",
  pitch: "#7C5CFC",
  design: "#ff9f0a",
  build: "#60A5FA",
  qa: "#E879A8",
  deployed: "#34C759",
  // Email statuses
  draft: "#ff9f0a",
  sent: "#34C759",
  failed: "#E879A8",
  // Task statuses
  pending: "#8e8e93",
  in_progress: "#60A5FA",
  completed: "#34C759",
};

export const STATUS_LABELS: Record<string, string> = {
  intake: "Intake",
  pitch: "Pitch",
  design: "Design",
  build: "Build",
  qa: "QA",
  deployed: "Deployed",
  draft: "Draft",
  sent: "Sent",
  failed: "Failed",
  pending: "Pending",
  in_progress: "In Progress",
  completed: "Completed",
};

export const PIPELINE_STAGES = [
  "intake",
  "pitch",
  "design",
  "build",
  "qa",
  "deployed",
] as const;

export const NAV_LINKS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/prospects", label: "Prospects", icon: Users },
  { href: "/projects", label: "Projects", icon: Rocket },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/emails", label: "Emails", icon: Mail },
  { href: "/messages", label: "Messages", icon: MessageSquare },
  { href: "/map", label: "Map", icon: Map },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
] as const;

export const MOBILE_NAV_MAIN = [
  { href: "/", label: "Home", icon: LayoutDashboard },
  { href: "/prospects", label: "Prospects", icon: Users },
  { href: "/projects", label: "Projects", icon: Rocket },
  { href: "/map", label: "Map", icon: Map },
] as const;

export const MOBILE_NAV_MORE = [
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/emails", label: "Emails", icon: Mail },
  { href: "/messages", label: "Messages", icon: MessageSquare },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
] as const;
