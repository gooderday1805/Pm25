"use client"

import { useEffect, useRef } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import type { PredictionData } from "./dashboard"

interface MapComponentProps {
  data: PredictionData
}

function getAQIColor(pm25: number): string {
  if (pm25 <= 12) return "#22c55e"
  if (pm25 <= 35) return "#eab308"
  if (pm25 <= 55) return "#f97316"
  if (pm25 <= 150) return "#ef4444"
  return "#a855f7"
}

export default function MapComponent({ data }: MapComponentProps) {
  const mapRef = useRef<L.Map | null>(null)

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map("map").setView([10.8231, 106.6297], 11)

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 19,
      }).addTo(mapRef.current)
    }

    const map = mapRef.current

    data.districts.forEach((district) => {
      const color = getAQIColor(district.pm25_prediction)
      const currentPM25 = district.raw_data?.air_quality?.pm2_5 || 0
      const temp = district.raw_data?.weather?.temperature_2m || 0
      const humidity = district.raw_data?.weather?.relative_humidity_2m || 0

      L.circleMarker([district.lat, district.lon], {
        radius: 10,
        fillColor: color,
        color: color,
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.7,
      })
        .bindPopup(
          `<div style="font-family: sans-serif">
            <strong>${district.name}</strong><br/>
            PM2.5 Dự đoán: ${district.pm25_prediction.toFixed(1)} μg/m³<br/>
            PM2.5 Hiện tại: ${currentPM25.toFixed(1)} μg/m³<br/>
            Nhiệt độ: ${temp.toFixed(1)}°C<br/>
            Độ ẩm: ${humidity.toFixed(1)}%
          </div>`,
        )
        .addTo(map)
    })

    return () => {
      // Cleanup on unmount
    }
  }, [data])

  return (
    <div className="space-y-4">
      <div id="map" className="h-[600px] rounded-lg border border-slate-600" />
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-green-500" />
          <span className="text-slate-400">Tốt</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-yellow-500" />
          <span className="text-slate-400">Trung bình</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-orange-500" />
          <span className="text-slate-400">Kém</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-red-500" />
          <span className="text-slate-400">Xấu</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-purple-500" />
          <span className="text-slate-400">Rất xấu</span>
        </div>
      </div>
    </div>
  )
}
