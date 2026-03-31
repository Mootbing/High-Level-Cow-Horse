"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { ProspectGeo } from "@/lib/types";
import { STATUS_COLORS } from "@/lib/constants";
import Link from "next/link";

function createIcon(color: string) {
  return L.divIcon({
    className: "",
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    html: `<div style="
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: ${color};
      border: 2.5px solid white;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    "></div>`,
  });
}

interface MapViewProps {
  prospects: ProspectGeo[];
  isLoading: boolean;
}

export default function MapView({ prospects, isLoading }: MapViewProps) {
  if (isLoading) {
    return (
      <div className="w-full flex items-center justify-center text-sm" style={{ height: "calc(100vh - 10rem)", color: "var(--text-light)" }}>
        Loading map...
      </div>
    );
  }

  const center: [number, number] =
    prospects.length > 0
      ? [
          prospects.reduce((s, p) => s + p.latitude, 0) / prospects.length,
          prospects.reduce((s, p) => s + p.longitude, 0) / prospects.length,
        ]
      : [39.8283, -98.5795];

  return (
    <MapContainer center={center} zoom={prospects.length > 0 ? 5 : 4} style={{ height: "calc(100vh - 10rem)", width: "100%" }} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
      />
      {prospects.map((p) => {
        const color = p.project_status ? STATUS_COLORS[p.project_status] || "#8e8e93" : "#8e8e93";
        return (
          <Marker key={p.id} position={[p.latitude, p.longitude]} icon={createIcon(color)}>
            <Popup>
              <div style={{ fontFamily: "Inter, system-ui, sans-serif", minWidth: 160 }}>
                <p style={{ fontWeight: 600, fontSize: 13, marginBottom: 4, color: "#0A0A0A" }}>
                  {p.company_name || "Unknown"}
                </p>
                {p.industry && (
                  <p style={{ fontSize: 11, color: "#6B6B6B", marginBottom: 4 }}>{p.industry}</p>
                )}
                {p.project_status && (
                  <p style={{ fontSize: 11, marginBottom: 6, color: "#6B6B6B" }}>
                    Status: <span style={{ color, fontWeight: 600 }}>{p.project_status}</span>
                  </p>
                )}
                <Link href={`/prospects/${p.id}`} style={{ fontSize: 11, color: "#7C5CFC", textDecoration: "underline" }}>
                  View details
                </Link>
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
