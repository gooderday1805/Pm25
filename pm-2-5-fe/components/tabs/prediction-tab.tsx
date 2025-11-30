"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { AlertCircle, Loader2 } from "lucide-react"
import type { PredictionData } from "../dashboard"
import DistrictCard from "../district-card"
import DistrictModal from "../district-modal"
import StatisticsPanel from "../statistics-panel"

interface PredictionTabProps {
  onPrediction: (data: PredictionData) => void
  onError: (error: string) => void
  initialData?: PredictionData | null
  selectedDate: string
  setSelectedDate: (date: string) => void
  selectedHour: string
  setSelectedHour: (hour: string) => void
  selectedMinute: string
  setSelectedMinute: (minute: string) => void
}

export default function PredictionTab({
  onPrediction,
  onError,
  initialData,
  selectedDate,
  setSelectedDate,
  selectedHour,
  setSelectedHour,
  selectedMinute,
  setSelectedMinute,
}: PredictionTabProps) {
  const [loading, setLoading] = useState(false)
  const [selectedDistrict, setSelectedDistrict] = useState<any>(null)
  const [showModal, setShowModal] = useState(false)
  const [predictionData, setPredictionData] = useState<PredictionData | null>(initialData || null)

  // Set default date (2 hours ago) only on first render
  useEffect(() => {
    if (!selectedDate) {
      const now = new Date()
      const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000)
      const formattedDate = twoHoursAgo.toISOString().split("T")[0]
      const hour = String(twoHoursAgo.getHours()).padStart(2, "0")

      setSelectedDate(formattedDate)
      setSelectedHour(hour)
    }
  }, [])

  const validateDateTime = (): { valid: boolean; errorCode?: string; errorMessage?: string } => {
    if (!selectedDate) {
      return { valid: false, errorCode: "MISSING_DATE", errorMessage: "Vui lòng chọn ngày" }
    }

    const now = new Date()
    const selectedDateTime = new Date(`${selectedDate}T${selectedHour}:${selectedMinute}:00`)

    // RULE 1: Check if target time is in future
    if (selectedDateTime > now) {
      const diffMs = selectedDateTime.getTime() - now.getTime()
      const diffHours = (diffMs / (1000 * 60 * 60)).toFixed(2)
      const diffMinutes = Math.ceil(diffMs / (1000 * 60))
      return {
        valid: false,
        errorCode: "FUTURE_TIME",
        errorMessage: `Không thể dự đoán. Vui lòng chọn thời gian trước ${now.toLocaleTimeString("vi-VN")}. Thời gian chọn cách hiện tại ${diffMinutes} phút.`,
      }
    }

    // RULE 2: Check if target time is too recent (< 30 minutes ago)
    const thirtyMinsAgo = new Date(now.getTime() - 30 * 60 * 1000)
    if (selectedDateTime > thirtyMinsAgo) {
      const diffMinutes = Math.ceil((thirtyMinsAgo.getTime() - selectedDateTime.getTime()) / (1000 * 60))
      return {
        valid: false,
        errorCode: "TIME_TOO_RECENT",
        errorMessage: `Dữ liệu chưa sẵn sàng. Vui lòng đợi thêm ${diffMinutes} phút hoặc chọn thời gian trước ${thirtyMinsAgo.toLocaleTimeString("vi-VN")}`,
      }
    }

    // RULE 3: Check if target time is too old (> 90 days)
    const ninetyDaysAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
    if (selectedDateTime < ninetyDaysAgo) {
      return {
        valid: false,
        errorCode: "TIME_TOO_OLD",
        errorMessage: "Thời gian quá xa trong quá khứ. Chỉ hỗ trợ dữ liệu trong vòng 90 ngày gần đây",
      }
    }

    return { valid: true }
  }

  const handlePredict = async () => {
    const validation = validateDateTime()
    if (!validation.valid) {
      onError(validation.errorMessage || "Lỗi xác thực")
      return
    }

    setLoading(true)
    onError("")

    try {
      const [year, month, day] = selectedDate.split("-").map(Number)
      const hour = Number(selectedHour)
      const minute = Number(selectedMinute)

      const response = await fetch("http://localhost:5001/api/v2/predict/all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ year, month, day, hour, minute }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        if (errorData.error) {
          const errorMsg = errorData.error.message || `API Error: ${response.status}`
          const errorCode = errorData.error.code
          onError(`[${errorCode}] ${errorMsg}`)
        } else {
          throw new Error(`API Error: ${response.status}`)
        }
        return
      }

      const data = await response.json()
      if (data.success) {
        setPredictionData(data.data)
        onPrediction({
          ...data.data,
          districts: data.data.districts || [],
        })
      } else {
        throw new Error(data.error?.message || "Lỗi dự đoán")
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Lỗi khi gọi API. Vui lòng kiểm tra backend."
      onError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Time Selection Card */}
      <Card className="border-slate-700 bg-slate-800/50 p-6">
        <h2 className="mb-4 text-lg font-semibold text-white">Chọn Thời Gian Dự Đoán</h2>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Ngày</label>
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="border-slate-600 bg-slate-700 text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Giờ</label>
            <select
              value={selectedHour}
              onChange={(e) => setSelectedHour(e.target.value)}
              className="w-full rounded-md border border-slate-600 bg-slate-700 px-3 py-2 text-white"
            >
              {Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0")).map((hour) => (
                <option key={hour} value={hour}>
                  {hour}:00
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Phút</label>
            <select
              value={selectedMinute}
              onChange={(e) => setSelectedMinute(e.target.value)}
              className="w-full rounded-md border border-slate-600 bg-slate-700 px-3 py-2 text-white"
            >
              {["0", "15", "30", "45"].map((minute) => (
                <option key={minute} value={minute}>
                  :{minute}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <Button
              onClick={handlePredict}
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Đang xử lý...
                </>
              ) : (
                "Dự Đoán Ngay"
              )}
            </Button>
          </div>
        </div>

        {predictionData && (
          <div className="mt-4 rounded-lg bg-blue-500/10 border border-blue-500/50 p-4">
            <p className="text-sm text-blue-300">{predictionData.prediction_info.explanation}</p>
          </div>
        )}
      </Card>

      {/* Statistics Panel */}
      {predictionData && <StatisticsPanel data={predictionData} />}

      {/* Districts Grid */}
      {predictionData && (
        <div>
          <h2 className="mb-4 text-lg font-semibold text-white">Kết Quả Dự Đoán - 24 Quận/Huyện</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {predictionData.districts.map((district) => (
              <DistrictCard
                key={district.id}
                district={district}
                onViewDetails={() => {
                  setSelectedDistrict(district)
                  setShowModal(true)
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* District Detail Modal */}
      {selectedDistrict && (
        <DistrictModal district={selectedDistrict} isOpen={showModal} onClose={() => setShowModal(false)} />
      )}

      {/* Empty State */}
      {!predictionData && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-12 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-slate-400 mb-3" />
          <p className="text-slate-400">Chọn thời gian và nhấn "Dự Đoán Ngay" để xem kết quả</p>
        </div>
      )}
    </div>
  )
}
