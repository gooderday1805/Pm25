"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MapPin, BarChart3, Home } from "lucide-react"
import PredictionTab from "./tabs/prediction-tab"
import MapTab from "./tabs/map-tab"
import AnalyticsTab from "./tabs/analytics-tab"

export interface PredictionData {
  districts: Array<{
    id: string
    name: string
    name_en: string
    pm25_prediction: number
    lat: number
    lon: number
    raw_data: {
      timestamp: string
      air_quality: {
        pm2_5: number
        pm10: number
        co: number
        no: number
        no2: number
        o3: number
        so2: number
        nh3: number
      }
      weather: {
        temperature_2m: number
        relative_humidity_2m: number
        precipitation: number
        pressure_msl: number
        windspeed_10m: number
        winddirection_10m: number
        shortwave_radiation: number
      }
    }
  }>
  statistics: {
    city_average: number
    city_max: number
    city_min: number
    city_median: number
    who_standard_15: { above: number; below: number }
    success_rate_percent: number
  }
  prediction_info: {
    target_time: string
    prediction_for: string
    explanation: string
  }
}

export default function Dashboard() {
  const [predictionData, setPredictionData] = useState<PredictionData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedDate, setSelectedDate] = useState<string>("")
  const [selectedHour, setSelectedHour] = useState<string>("")
  const [selectedMinute, setSelectedMinute] = useState<string>("0")

  const handlePrediction = (data: PredictionData) => {
    setPredictionData(data)
    setError(null)
  }

  const handleError = (errorMsg: string) => {
    setError(errorMsg)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-gradient-to-br from-blue-400 to-blue-600 p-3">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">PM2.5 Dashboard</h1>
                <p className="text-sm text-slate-400">TP. Hồ Chí Minh - Dự Đoán Chất Lượng Không Khí</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-500/50 bg-red-500/10 p-4">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        <Tabs defaultValue="prediction" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800/50 p-1">
            <TabsTrigger value="prediction" className="flex items-center gap-2">
              <Home className="h-4 w-4" />
              <span className="hidden sm:inline">Dự Đoán</span>
            </TabsTrigger>
            <TabsTrigger value="map" className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              <span className="hidden sm:inline">Bản Đồ</span>
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Phân Tích</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="prediction" className="mt-6">
            <PredictionTab
              onPrediction={handlePrediction}
              onError={handleError}
              initialData={predictionData}
              selectedDate={selectedDate}
              setSelectedDate={setSelectedDate}
              selectedHour={selectedHour}
              setSelectedHour={setSelectedHour}
              selectedMinute={selectedMinute}
              setSelectedMinute={setSelectedMinute}
            />
          </TabsContent>

          <TabsContent value="map" className="mt-6">
            <MapTab data={predictionData} />
          </TabsContent>

          <TabsContent value="analytics" className="mt-6">
            <AnalyticsTab data={predictionData} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
