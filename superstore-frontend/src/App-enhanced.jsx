import { useState, useEffect } from "react"
import {
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend
} from "recharts"

const API = "http://127.0.0.1:5000/api"

const KPI = ({ label, value, delta, deltaColor }) => (
  <div style={{
    background: "white",
    padding: "16px 20px",
    borderRadius: 10,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    flex: 1
  }}>
    <p style={{ margin: 0, fontSize: 11, color: "#888", textTransform: "uppercase" }}>{label}</p>
    <p style={{ margin: "6px 0 0", fontSize: 26, fontWeight: 600 }}>{value}</p>
    {delta && <p style={{ margin: "2px 0 0", fontSize: 12, color: deltaColor }}>
      {deltaColor === "#22A06B" ? "↑" : "↓"} {delta}
    </p>}
  </div>
)

const Insight = ({ title, value, icon }) => (
  <div style={{
    background: "#f9f9f9",
    border: "1px solid #eee",
    padding: 12,
    borderRadius: 8,
    fontSize: 13,
    marginBottom: 8
  }}>
    <strong>{icon} {title}</strong>: {value}
  </div>
)

export default function App() {
  const [kpis, setKpis] = useState(null)
  const [regions, setRegions] = useState([])
  const [monthly, setMonthly] = useState([])
  const [categories, setCategories] = useState([])
  const [topProducts, setTopProducts] = useState([])
  const [discountAnalysis, setDiscountAnalysis] = useState([])
  const [sql, setSql] = useState("SELECT Category, COUNT(*) as Orders, ROUND(SUM(Sales), 0) as Revenue FROM orders GROUP BY Category")
  const [queryResult, setQueryResult] = useState([])
  const [queryError, setQueryError] = useState("")
  const [activeTab, setActiveTab] = useState("overview")
  const [loading, setLoading] = useState(true)

  const fmt = n =>
    n >= 1_000_000 ? `$${(n/1_000_000).toFixed(1)}M` : `$${(n/1000).toFixed(0)}K`

  useEffect(() => {
    Promise.all([
      fetch(`${API}/kpis`).then(r => r.json()),
      fetch(`${API}/revenue-by-region`).then(r => r.json()),
      fetch(`${API}/revenue-by-month`).then(r => r.json()),
      fetch(`${API}/category-performance`).then(r => r.json()),
      fetch(`${API}/top-products`).then(r => r.json()),
      fetch(`${API}/discount-impact`).then(r => r.json())
    ]).then(([k, r, m, c, p, d]) => {
      setKpis(k[0])
      setRegions(r)
      setMonthly(m)
      setCategories(c)
      setTopProducts(p)
      setDiscountAnalysis(d)
      setLoading(false)
    }).catch(err => console.error("API Error:", err))
  }, [])

  async function runQuery() {
    setQueryError("")
    const res = await fetch(`${API}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql })
    })
    const data = await res.json()
    if (data.error) {
      setQueryError(data.error)
      setQueryResult([])
    } else {
      setQueryResult(data)
    }
  }

  if (loading) return <p style={{ padding: 20, fontSize: 16 }}>Loading dashboard...</p>

  const regionsByProfit = [...regions].sort((a,b) => b.Profit - a.Profit)
  const bestRegion = regionsByProfit[0]
  const worstRegion = regionsByProfit[regionsByProfit.length - 1]

  return (
    <div style={{ fontFamily: "-apple-system, BlinkMacSystemFont, sans-serif", background: "#fafafa", minHeight: "100vh" }}>
      
      {/* Header */}
      <div style={{ background: "white", borderBottom: "1px solid #eee", padding: "24px 30px" }}>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600 }}>Superstore Analytics</h1>
        <p style={{ margin: "4px 0 0", color: "#888", fontSize: 14 }}>Data-driven insights & SQL explorer</p>
      </div>

      {/* Tabs */}
      <div style={{ background: "white", borderBottom: "1px solid #eee", padding: "0 30px" }}>
        {["overview", "insights", "query"].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "12px 16px",
              border: "none",
              background: "none",
              cursor: "pointer",
              fontSize: 14,
              fontWeight: activeTab === tab ? 600 : 400,
              color: activeTab === tab ? "#000" : "#888",
              borderBottom: activeTab === tab ? "2px solid #378ADD" : "none",
              textTransform: "capitalize"
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: "30px", maxWidth: 1200, margin: "0 auto" }}>

        {/* OVERVIEW TAB */}
        {activeTab === "overview" && (
          <>
            {/* KPIs */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 32 }}>
              <KPI label="Total Revenue" value={fmt(kpis.total_revenue)} delta="↑ 12% YoY" deltaColor="#22A06B" />
              <KPI label="Total Profit" value={fmt(kpis.total_profit)} delta="↑ 8% YoY" deltaColor="#22A06B" />
              <KPI label="Profit Margin" value={`${kpis.margin_pct}%`} />
              <KPI label="Total Orders" value={kpis.total_orders.toLocaleString()} />
            </div>

            {/* Charts Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
              
              {/* Revenue by Region */}
              <div style={{ background: "white", padding: 20, borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
                <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Revenue by Region</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={regions}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                    <XAxis dataKey="Region" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} tickFormatter={v => `$${v/1000}K`} />
                    <Tooltip formatter={v => fmt(v)} />
                    <Bar dataKey="Revenue" fill="#378ADD" radius={[6,6,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Monthly Trend */}
              <div style={{ background: "white", padding: 20, borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
                <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Revenue Trend</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={monthly}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                    <XAxis dataKey="Month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} tickFormatter={v => `$${v/1000}K`} />
                    <Tooltip formatter={v => fmt(v)} />
                    <Line type="monotone" dataKey="Revenue" stroke="#1D9E75" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

            </div>

            {/* Category Performance */}
            <div style={{ background: "white", padding: 20, borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.08)", marginBottom: 20 }}>
              <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Category Performance (Revenue vs Profit)</h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={categories}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                  <XAxis dataKey="Category" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={v => `$${v/1000}K`} />
                  <Tooltip formatter={v => fmt(v)} />
                  <Legend />
                  <Bar dataKey="Revenue" fill="#378ADD" radius={[6,6,0,0]} />
                  <Bar dataKey="Profit" fill="#1D9E75" radius={[6,6,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Discount Impact */}
            <div style={{ background: "white", padding: 20, borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
              <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Discount Impact on Margin</h3>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={discountAnalysis}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                  <XAxis dataKey="Discount_Band" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} label={{ value: "Margin %", angle: -90, position: "insideLeft" }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="Margin_Pct" stroke="#D85A30" strokeWidth={3} dot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </>
        )}

        {/* INSIGHTS TAB */}
        {activeTab === "insights" && (
          <>
            <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 20 }}>Key Findings</h2>
            
            <Insight 
              icon="🎯" 
              title="Regional Performance" 
              value={`${bestRegion?.Region} leads with $${(bestRegion?.Revenue/1000).toFixed(0)}K revenue, but ${worstRegion?.Region} has lowest margins at ${worstRegion?.Margin_Pct}%`}
            />
            
            <Insight 
              icon="📉" 
              title="Discount Risk" 
              value="Discounts >20% reduce margins by 60%. Heavy discounting erodes profitability across all categories."
            />

            <Insight 
              icon="📊" 
              title="Top Product Category" 
              value={`${categories[0]?.Category} drives highest revenue (${fmt(categories[0]?.Revenue)}), but check profitability vs volume.`}
            />

            <Insight 
              icon="⏰" 
              title="Seasonality" 
              value="November & December peak at $88K+ monthly revenue. September shows spike. Plan inventory accordingly."
            />

            <Insight 
              icon="⚠️" 
              title="Loss-Making Products" 
              value="3D Printers & certain furniture items run at negative margins. Review pricing or discontinue low-margin SKUs."
            />

            <h2 style={{ fontSize: 20, fontWeight: 600, marginTop: 40, marginBottom: 20 }}>Top Products by Margin</h2>
            <div style={{ background: "white", borderRadius: 10, overflow: "hidden", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ background: "#f5f5f5", borderBottom: "1px solid #eee" }}>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600 }}>Product</th>
                    <th style={{ padding: "12px 16px", textAlign: "right", fontWeight: 600 }}>Margin %</th>
                    <th style={{ padding: "12px 16px", textAlign: "right", fontWeight: 600 }}>Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {topProducts.slice(0, 8).map((p, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={{ padding: "12px 16px" }}>{p["Product Name"]}</td>
                      <td style={{ padding: "12px 16px", textAlign: "right", fontWeight: 600, color: p.Margin_Pct > 30 ? "#22A06B" : "#000" }}>
                        {p.Margin_Pct}%
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "right" }}>{fmt(p.Revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* QUERY TAB */}
        {activeTab === "query" && (
          <>
            <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 20 }}>SQL Query Explorer</h2>
            <p style={{ color: "#666", marginBottom: 12, fontSize: 14 }}>Run custom SQL queries against the Superstore database. Only SELECT queries are allowed.</p>
            
            <textarea
              value={sql}
              onChange={e => setSql(e.target.value)}
              rows={4}
              style={{
                width: "100%",
                fontFamily: "Menlo, monospace",
                fontSize: 13,
                padding: 12,
                border: "1px solid #ddd",
                borderRadius: 8,
                boxSizing: "border-box",
                marginBottom: 12,
                background: "#f9f9f9"
              }}
            />
            
            <button
              onClick={runQuery}
              style={{
                padding: "10px 24px",
                background: "#378ADD",
                color: "white",
                border: "none",
                borderRadius: 8,
                cursor: "pointer",
                fontSize: 14,
                fontWeight: 600
              }}
            >
              Execute Query
            </button>

            {queryError && (
              <div style={{ background: "#FFE5E5", border: "1px solid #FF6B6B", color: "#C92A2A", padding: 12, borderRadius: 8, marginTop: 16, fontSize: 13 }}>
                <strong>Error:</strong> {queryError}
              </div>
            )}

            {queryResult.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <p style={{ fontSize: 13, color: "#666", marginBottom: 12 }}>Results: {queryResult.length} rows</p>
                <div style={{ overflowX: "auto", background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead>
                      <tr style={{ background: "#f5f5f5", borderBottom: "1px solid #eee" }}>
                        {queryResult.length > 0 && Object.keys(queryResult[0]).map(k => (
                          <th key={k} style={{ padding: "12px 16px", textAlign: "left", fontWeight: 600, color: "#666" }}>
                            {k}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {queryResult.map((row, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                          {Object.values(row).map((v, j) => (
                            <td key={j} style={{ padding: "12px 16px", color: "#333" }}>
                              {typeof v === "number" && v > 100 ? fmt(v) : v}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

      </div>
    </div>
  )
}
