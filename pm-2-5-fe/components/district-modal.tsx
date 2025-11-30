"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Wind, Droplets, Thermometer, Gauge, Cloud, Zap } from "lucide-react"

interface DistrictModalProps {
  district: any
  isOpen: boolean
  onClose: () => void
}

function getAQIBadgeColor(pm25: number) {
  if (pm25 <= 12) return "bg-green-500/20 text-green-300"
  if (pm25 <= 35) return "bg-yellow-500/20 text-yellow-300"
  if (pm25 <= 55) return "bg-orange-500/20 text-orange-300"
  if (pm25 <= 150) return "bg-red-500/20 text-red-300"
  return "bg-purple-500/20 text-purple-300"
}

export default function DistrictModal({ district, isOpen, onClose }: DistrictModalProps) {
  const airQuality = district.raw_data?.air_quality || {}
  const weather = district.raw_data?.weather || {}

  const airQualityData = [
    { name: "PM2.5", value: airQuality.pm2_5?.toFixed(2), unit: "μg/m³", icon: Gauge },
    { name: "PM10", value: airQuality.pm10?.toFixed(2), unit: "μg/m³", icon: Gauge },
    { name: "CO", value: airQuality.co?.toFixed(3), unit: "mg/m³", icon: Zap },
    { name: "NO", value: airQuality.no?.toFixed(2), unit: "μg/m³", icon: Cloud },
    { name: "NO₂", value: airQuality.no2?.toFixed(2), unit: "μg/m³", icon: Cloud },
    { name: "O₃", value: airQuality.o3?.toFixed(2), unit: "μg/m³", icon: Cloud },
    { name: "SO₂", value: airQuality.so2?.toFixed(2), unit: "μg/m³", icon: Cloud },
    { name: "NH₃", value: airQuality.nh3?.toFixed(2), unit: "μg/m³", icon: Cloud },
  ]

  const weatherData = [
    { name: "Nhiệt độ", value: weather.temperature_2m?.toFixed(1), unit: "°C", icon: Thermometer },
    { name: "Độ ẩm", value: weather.relative_humidity_2m?.toFixed(1), unit: "%", icon: Droplets },
    { name: "Lượng mưa", value: weather.precipitation?.toFixed(2), unit: "mm", icon: Cloud },
    { name: "Áp suất", value: weather.pressure_msl?.toFixed(1), unit: "hPa", icon: Gauge },
    { name: "Tốc độ gió", value: weather.windspeed_10m?.toFixed(1), unit: "m/s", icon: Wind },
    { name: "Hướng gió", value: weather.winddirection_10m?.toFixed(0), unit: "°", icon: Wind },
    { name: "Bức xạ", value: weather.shortwave_radiation?.toFixed(1), unit: "W/m²", icon: Zap },
  ]

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="border-slate-700 bg-slate-900 max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-2xl font-bold text-white">{district.name}</DialogTitle>
              <p className="text-sm text-slate-400 mt-1">{district.name_en}</p>
            </div>
            <span
              className={`${getAQIBadgeColor(district.pm25_prediction)} px-3 py-1 rounded-lg text-sm font-semibold`}
            >
              PM2.5: {district.pm25_prediction.toFixed(1)}
            </span>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Air Quality Section */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Chất Lượng Không Khí</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {airQualityData.map((item) => {
                const Icon = item.icon
                return (
                  <div key={item.name} className="rounded-lg bg-slate-800/50 border border-slate-700 p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className="h-4 w-4 text-blue-400" />
                      <span className="text-xs font-medium text-slate-400">{item.name}</span>
                    </div>
                    <div className="text-lg font-bold text-white">
                      {item.value || "N/A"}
                      <span className="text-xs ml-1 text-slate-400">{item.unit}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Weather Section */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Thời Tiết</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {weatherData.map((item) => {
                const Icon = item.icon
                return (
                  <div key={item.name} className="rounded-lg bg-slate-800/50 border border-slate-700 p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className="h-4 w-4 text-cyan-400" />
                      <span className="text-xs font-medium text-slate-400">{item.name}</span>
                    </div>
                    <div className="text-lg font-bold text-white">
                      {item.value || "N/A"}
                      <span className="text-xs ml-1 text-slate-400">{item.unit}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
