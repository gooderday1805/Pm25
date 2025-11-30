"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Eye } from "lucide-react"

interface DistrictCardProps {
  district: any
  onViewDetails: () => void
}

function getAQIColor(pm25: number): { bg: string; text: string; badge: string; icon: string } {
  if (pm25 <= 12) {
    return {
      bg: "bg-green-500/10",
      text: "text-green-400",
      badge: "bg-green-500/20 text-green-300",
      icon: "text-green-400",
    }
  } else if (pm25 <= 35) {
    return {
      bg: "bg-yellow-500/10",
      text: "text-yellow-400",
      badge: "bg-yellow-500/20 text-yellow-300",
      icon: "text-yellow-400",
    }
  } else if (pm25 <= 55) {
    return {
      bg: "bg-orange-500/10",
      text: "text-orange-400",
      badge: "bg-orange-500/20 text-orange-300",
      icon: "text-orange-400",
    }
  } else if (pm25 <= 150) {
    return { bg: "bg-red-500/10", text: "text-red-400", badge: "bg-red-500/20 text-red-300", icon: "text-red-400" }
  } else {
    return {
      bg: "bg-purple-500/10",
      text: "text-purple-400",
      badge: "bg-purple-500/20 text-purple-300",
      icon: "text-purple-400",
    }
  }
}

function getAQILabel(pm25: number): string {
  if (pm25 <= 12) return "Tốt"
  if (pm25 <= 35) return "Trung bình"
  if (pm25 <= 55) return "Kém"
  if (pm25 <= 150) return "Xấu"
  return "Rất xấu"
}

export default function DistrictCard({ district, onViewDetails }: DistrictCardProps) {
  const colors = getAQIColor(district.pm25_prediction)
  const label = getAQILabel(district.pm25_prediction)
  const currentPM25 = district.raw_data?.air_quality?.pm2_5

  return (
    <Card className={`border-slate-700 ${colors.bg} p-4 hover:border-slate-600 transition-all`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-white mb-1">{district.name}</h3>
          <span className={`${colors.badge} px-2 py-1 rounded text-xs font-medium`}>{label}</span>
        </div>
      </div>

      <div className={`text-3xl font-bold ${colors.text} mb-2`}>
        {district.pm25_prediction.toFixed(1)}
        <span className="text-sm ml-1 opacity-75">μg/m³</span>
      </div>

      {currentPM25 && (
        <div className="text-xs text-slate-400 mb-3 flex items-center gap-1">
          <span>Hiện tại: {currentPM25.toFixed(1)}</span>
        </div>
      )}

      <Button
        onClick={onViewDetails}
        variant="outline"
        size="sm"
        className="w-full border-slate-600 hover:bg-slate-700/50 text-slate-300 bg-transparent"
      >
        <Eye className="h-4 w-4 mr-2" />
        Xem Chi Tiết
      </Button>
    </Card>
  )
}
