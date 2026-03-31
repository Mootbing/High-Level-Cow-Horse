"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 30000,
  });
}

export function useProspects(params?: Parameters<typeof api.getProspects>[0]) {
  return useQuery({
    queryKey: ["prospects", params],
    queryFn: () => api.getProspects(params),
  });
}

export function useProspect(id: string) {
  return useQuery({
    queryKey: ["prospect", id],
    queryFn: () => api.getProspect(id),
    enabled: !!id,
  });
}

export function useProspectsGeo() {
  return useQuery({
    queryKey: ["prospects-geo"],
    queryFn: () => api.getProspectsGeo(),
  });
}

export function useProjects(params?: Parameters<typeof api.getProjects>[0]) {
  return useQuery({
    queryKey: ["projects", params],
    queryFn: () => api.getProjects(params),
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => api.getProject(id),
    enabled: !!id,
  });
}

export function useProjectStats() {
  return useQuery({
    queryKey: ["project-stats"],
    queryFn: () => api.getProjectStats(),
  });
}

export function useProjectTasks(id: string) {
  return useQuery({
    queryKey: ["project-tasks", id],
    queryFn: () => api.getProjectTasks(id),
    enabled: !!id,
  });
}

export function useProjectDeployments(id: string) {
  return useQuery({
    queryKey: ["project-deployments", id],
    queryFn: () => api.getProjectDeployments(id),
    enabled: !!id,
  });
}

export function useEmails(params?: Parameters<typeof api.getEmails>[0]) {
  return useQuery({
    queryKey: ["emails", params],
    queryFn: () => api.getEmails(params),
  });
}

export function useMessages(params?: Parameters<typeof api.getMessages>[0]) {
  return useQuery({
    queryKey: ["messages", params],
    queryFn: () => api.getMessages(params),
  });
}

export function useKnowledge(params?: Parameters<typeof api.getKnowledge>[0]) {
  return useQuery({
    queryKey: ["knowledge", params],
    queryFn: () => api.getKnowledge(params),
  });
}

export function useMetrics(days?: number) {
  return useQuery({
    queryKey: ["metrics", days],
    queryFn: () => api.getMetrics(days),
  });
}
