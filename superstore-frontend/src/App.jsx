import { useState, useEffect } from "react"
import {
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts"

const API = "http://127.0.0.1:5000/api"

const Card = ({ title, value }) => (
  <div style={{
    background: "white",
    padding: 16,
    borderRadius: 12,
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
    flex: 1
  }}>
    <p style={{ margin: 0, fontSize: 12, color: "#777" }}>{title}</p>
    <h2 style={{ margin: 0 }}>{value}</h2>
  </div>
)

export default function App() {
  const [kpis, setKpis] = useState(null)
  const [regions, setRegions] = useState([])
  const [monthly, setMonthly] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  const fmt = n =>
    n >= 1_000_000 ? `$${(n/1_000_000).toFixed(1)}M` : `$${(n/1000).toFixed(0)}K`

  useEffect(() => {
    Promise.all([
      fetch(`${API}/kpis`).then(r => r.json()),
      fetch(`${API}/revenue-by-region`).then(r => r.json()),
      fetch(`${API}/revenue-by-month`).then(r => r.json()),
      fetch(`${API}/category-performance`).then(r => r.json())
    ]).then(([k, r, m, c]) => {
      setKpis(k.data)
      setRegions(r.data)
      setMonthly(m.data)
      setCategories(c.data)
      setLoading(false)
    })
  }, [])

  if (loading) return <p style={{ padding: 20 }}>Loading dashboard...</p>

  return (
    <div style={{ fontFamily: "sans-serif", padding: 30, maxWidth: 1100, margin: "0 auto" }}>

      <h1>📊 Superstore Analytics Dashboard</h1>

      {/* KPI ROW */}
      <div style={{ display: "flex", gap: 12 }}>
        <Card title="Revenue" value={fmt(kpis.revenue)} />
        <Card title="Profit" value={fmt(kpis.profit)} />
        <Card title="Margin %" value={`${kpis.margin}%`} />
        <Card title="Orders" value={kpis.orders} />
      </div>

      {/* REGION */}
      <h3 style={{ marginTop: 40 }}>Revenue by Region</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={regions}>
          <CartesianGrid />
          <XAxis dataKey="Region" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="revenue" fill="#4F8EF7" />
        </BarChart>
      </ResponsiveContainer>

      {/* MONTH */}
      <h3>Revenue Over Time</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={monthly}>
          <CartesianGrid />
          <XAxis dataKey="Month" 
          label={{ value: "Month", position: "insideBottom", offset: -5 }}/>
          <YAxis />
          <Tooltip />
          <Line dataKey="revenue" stroke="#22A06B" />
        </LineChart>
      </ResponsiveContainer>

      {/* CATEGORY */}
      <h3>Category Performance</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={categories}>
          <CartesianGrid />
          <XAxis dataKey="Category" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="revenue" fill="#4F8EF7" />
          <Bar dataKey="profit" fill="#22A06B" />
        </BarChart>
      </ResponsiveContainer>

    </div>
  )
}
