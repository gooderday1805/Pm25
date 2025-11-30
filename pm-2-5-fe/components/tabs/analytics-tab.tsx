"use client"

import { useMemo } from "react"
import { Card } from "@/components/ui/card"
import { AlertCircle } from "lucide-react"
import type { PredictionData } from "../dashboard"
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"

interface AnalyticsTabProps {
  data: PredictionData | null
}

const COLORS = ["#22c55e", "#eab308", "#f97316", "#ef4444", "#a855f7"]

export default function AnalyticsTab({ data }: AnalyticsTabProps) {
  const barChartData = useMemo(() => {
    return data
      ? data.districts
          .slice()
          .sort((a, b) => b.pm25_prediction - a.pm25_prediction)
          .map((d) => ({
            name: d.name.substring(0, 10),
            value: Number.parseFloat(d.pm25_prediction.toFixed(1)),
            fullName: d.name,
          }))
      : []
  }, [data])

  const pieChartData = useMemo(() => {
    if (!data) return []
    const categories = {
      good: data.districts.filter((d) => d.pm25_prediction <= 12).length,
      moderate: data.districts.filter((d) => d.pm25_prediction > 12 && d.pm25_prediction <= 35).length,
      poor: data.districts.filter((d) => d.pm25_prediction > 35 && d.pm25_prediction <= 55).length,
      bad: data.districts.filter((d) => d.pm25_prediction > 55).length,
    }

    return [
      { name: "Tốt (0-12)", value: categories.good, color: "#22c55e" },
      { name: "Trung bình (12-35)", value: categories.moderate, color: "#eab308" },
      { name: "Kém (35-55)", value: categories.poor, color: "#f97316" },
      { name: "Xấu (>55)", value: categories.bad, color: "#ef4444" },
    ]
  }, [data])

  const topPolluted = useMemo(() => {
    if (!data) return []
    return data.districts
      .slice()
      .sort((a, b) => b.pm25_prediction - a.pm25_prediction)
      .slice(0, 5)
      .map((d, i) => ({ rank: i + 1, name: d.name, value: d.pm25_prediction.toFixed(1) }))
  }, [data])

  const topClean = useMemo(() => {
    if (!data) return []
    return data.districts
      .slice()
      .sort((a, b) => a.pm25_prediction - b.pm25_prediction)
      .slice(0, 5)
      .map((d, i) => ({ rank: i + 1, name: d.name, value: d.pm25_prediction.toFixed(1) }))
  }, [data])

  return (
    <div className="space-y-6">
      {/* Bar Chart */}
      <Card className="border-slate-700 bg-slate-800/50 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Xếp Hạng PM2.5 các Quận/Huyện</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barChartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" tick={{ fill: "#9ca3af" }} angle={-45} textAnchor="end" height={80} />
            <YAxis tick={{ fill: "#9ca3af" }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: "6px" }}
              labelStyle={{ color: "#f3f4f6" }}
            />
            <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Pie Charts Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Quality Distribution Pie */}
        <Card className="border-slate-700 bg-slate-800/50 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Phân Bố Chất Lượng Không Khí</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieChartData}
                cx="50%"
                cy="40%"
                labelLine={false}
                outerRadius={70}
                fill="#8884d8"
                dataKey="value"
              >
                {pieChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value, entry) => `${entry.payload.name}: ${entry.payload.value}`}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: "6px" }}
                labelStyle={{ color: "#f3f4f6" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Statistics Cards */}
        <div className="space-y-3">
          {data && (
            <>
              <Card className="border-slate-700 bg-slate-800/50 p-4">
                <p className="text-sm text-slate-400 mb-1">Độ Lệch Chuẩn</p>
                <p className="text-2xl font-bold text-white">
                  {Math.sqrt(
                    data.districts.reduce((acc, d) => {
                      const mean = data.statistics.city_average
                      return acc + Math.pow(d.pm25_prediction - mean, 2)
                    }, 0) / data.districts.length,
                  ).toFixed(2)}
                  <span className="text-xs ml-1 text-slate-400">μg/m³</span>
                </p>
              </Card>

              <Card className="border-slate-700 bg-slate-800/50 p-4">
                <p className="text-sm text-slate-400 mb-1">Trung Vị</p>
                <p className="text-2xl font-bold text-white">
                  {data.statistics.city_median.toFixed(1)}
                  <span className="text-xs ml-1 text-slate-400">μg/m³</span>
                </p>
              </Card>

              <Card className="border-slate-700 bg-slate-800/50 p-4">
                <p className="text-sm text-slate-400 mb-1">Tỷ Lệ Thành Công</p>
                <p className="text-2xl font-bold text-white">
                  {data.statistics.success_rate_percent.toFixed(1)}
                  <span className="text-xs ml-1 text-slate-400">%</span>
                </p>
              </Card>

              <Card className="border-slate-700 bg-slate-800/50 p-4">
                <p className="text-sm text-slate-400 mb-1">Vượt Chuẩn WHO</p>
                <p className="text-2xl font-bold text-red-400">
                  {data.statistics.who_standard_15.above}/{data.districts.length}
                  <span className="text-xs ml-1 text-slate-400">quận</span>
                </p>
              </Card>
            </>
          )}
        </div>
      </div>

      {/* Top Tables */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-slate-700 bg-slate-800/50 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Top 5 Ô Nhiễm Nhất</h2>
          <div className="space-y-2">
            {topPolluted.map((item) => (
              <div key={item.rank} className="flex items-center justify-between p-2 rounded bg-red-500/10">
                <span className="text-sm font-medium text-slate-300">
                  {item.rank}. {item.name}
                </span>
                <span className="text-sm font-bold text-red-400">{item.value} μg/m³</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="border-slate-700 bg-slate-800/50 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Top 5 Sạch Nhất</h2>
          <div className="space-y-2">
            {topClean.map((item) => (
              <div key={item.rank} className="flex items-center justify-between p-2 rounded bg-green-500/10">
                <span className="text-sm font-medium text-slate-300">
                  {item.rank}. {item.name}
                </span>
                <span className="text-sm font-bold text-green-400">{item.value} μg/m³</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
      {!data && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-12 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-slate-400 mb-3" />
          <p className="text-slate-400">Vui lòng dự đoán ở Tab 1 trước để xem phân tích</p>
        </div>
      )}
    </div>
  )
}
