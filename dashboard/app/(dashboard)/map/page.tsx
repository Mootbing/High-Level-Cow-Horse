"use client";

import dynamic from "next/dynamic";
import { useProspectsGeo } from "@/lib/hooks/use-api";
import { Globe } from "lucide-react";

const MapView = dynamic(() => import("@/components/map/map-container"), {
  ssr: false,
  loading: () => (
    <div className="w-full skeleton" style={{ height: "calc(100vh - 10rem)", borderRadius: "var(--radius-lg)" }} />
  ),
});

export default function MapPage() {
  const { data: prospects, isLoading } = useProspectsGeo();

  return (
    <div className="space-y-4 animate-in">
      <div className="flex items-center gap-2">
        <Globe size={15} style={{ color: "var(--accent)" }} />
        <span className="text-label">
          {prospects?.length || 0} geocoded prospects
        </span>
      </div>

      <div className="card-static p-0 overflow-hidden">
        <MapView prospects={prospects || []} isLoading={isLoading} />
      </div>
    </div>
  );
}
