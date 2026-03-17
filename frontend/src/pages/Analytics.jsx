import React, { useCallback, useEffect, useState } from 'react'
import {
  PieChart,
  Pie,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { FaServer, FaDatabase, FaSpinner } from 'react-icons/fa'
import { apiService } from '../utils/api'

function Analytics() {
  const [stats, setStats] = useState(null)
  const [health, setHealth] = useState(null)
  const [softSkills, setSoftSkills] = useState({
    communication: 0,
    leadership: 0,
    problemSolving: 0,
  })
  const [localMetrics, setLocalMetrics] = useState({
    queriesProcessed: 0,
    bias: { total: 0, clean: 0, biased: 0, types: { age: 0, gender: 0, language: 0 } },
    soft: { count: 0, communication_total: 0, leadership_total: 0, problem_solving_total: 0 },
  })
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')

  const safeJsonParse = useCallback((value, fallback) => {
    try {
      if (!value) return fallback
      return JSON.parse(value)
    } catch {
      return fallback
    }
  }, [])

  const loadLocalMetrics = useCallback(() => {
    const queriesProcessed = parseInt(localStorage.getItem('rms_queries_processed') || '0', 10) || 0
    const bias = safeJsonParse(localStorage.getItem('rms_bias_stats'), {
      total: 0,
      clean: 0,
      biased: 0,
      types: { age: 0, gender: 0, language: 0 },
    })
    const softSkillsData = JSON.parse(localStorage.getItem('softSkillsData') || '[]')
    if (softSkillsData.length > 0) {
      const avg = (key) =>
        Math.round(
          softSkillsData.reduce((sum, s) => sum + (s?.[key] || 0), 0) /
            softSkillsData.length
        )
      setSoftSkills({
        communication: avg('communication_score'),
        leadership: avg('leadership_score'),
        problemSolving: avg('problem_solving_score'),
      })
    } else {
      setSoftSkills({ communication: 0, leadership: 0, problemSolving: 0 })
    }
    const soft = softSkillsData.reduce(
      (acc, s) => {
        const communication = Number(s?.communication_score)
        const leadership = Number(s?.leadership_score)
        const problemSolving = Number(s?.problem_solving_score)

        if (Number.isFinite(communication) && Number.isFinite(leadership) && Number.isFinite(problemSolving)) {
          acc.count += 1
          acc.communication_total += communication
          acc.leadership_total += leadership
          acc.problem_solving_total += problemSolving
        }
        return acc
      },
      { count: 0, communication_total: 0, leadership_total: 0, problem_solving_total: 0 }
    )

    setLocalMetrics({ queriesProcessed, bias, soft })
  }, [safeJsonParse])

  const fetchData = useCallback(
    async ({ showLoader } = { showLoader: false }) => {
      try {
        if (showLoader) setLoading(true)
        else setRefreshing(true)

        const [statsData, gatewayHealthData] = await Promise.all([
          apiService.getStats(),
          apiService.checkHealth(),
        ])

        setStats(statsData)
        setHealth(gatewayHealthData)
        loadLocalMetrics()
        setError('')
      } catch (err) {
        setError('Failed to load analytics data')
        console.error('Error:', err)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [loadLocalMetrics]
  )

  useEffect(() => {
    fetchData({ showLoader: true })
    const onStorage = () => loadLocalMetrics()
    window.addEventListener('storage', onStorage)

    const raw = JSON.parse(localStorage.getItem('softSkillsData') || '[]')
    if (raw.length > 0) {
      const avg = (key) =>
        Math.round(raw.reduce((sum, s) => sum + (s[key] || 0), 0) / raw.length)
      setSoftSkills({
        communication: avg('communication_score'),
        leadership: avg('leadership_score'),
        problemSolving: avg('problem_solving_score'),
      })
    }

    return () => {
      window.removeEventListener('storage', onStorage)
    }
  }, [fetchData, loadLocalMetrics])

  const COLORS = ['#7c3aed', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-dark-text/70">Loading analytics...</p>
        </div>
      </div>
    )
  }

  const statusDot = (ok) =>
    `inline-block w-2.5 h-2.5 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'}`

  const baselineExecutionTime = '15-20s'
  const avgTokensPerQuery = 573
  const estimatedCostPerQuery = 0.00014

  const biasData = JSON.parse(localStorage.getItem('biasData') || '[]')
  const biasedCount = biasData.filter((b) => b?.has_bias === true).length
  const cleanCount = biasData.filter((b) => b?.has_bias === false).length
  const total = biasedCount + cleanCount
  const biasFreePct = total > 0 ? Math.round((cleanCount / total) * 100) : 100

  const biasTypeCounts = biasData.reduce(
    (acc, b) => {
      if (b?.has_bias !== true) return acc
      const types = Array.isArray(b?.bias_types) ? b.bias_types : []
      if (types.some((t) => String(t).includes('age'))) acc.age += 1
      if (types.some((t) => String(t).includes('gender'))) acc.gender += 1
      if (types.some((t) => String(t).includes('cultural') || String(t).includes('language'))) acc.language += 1
      return acc
    },
    { age: 0, gender: 0, language: 0 }
  )

  const biasPieData = [
    { name: 'Age', count: biasTypeCounts.age },
    { name: 'Gender', count: biasTypeCounts.gender },
    { name: 'Language', count: biasTypeCounts.language },
  ]

  const softCount = localMetrics.soft.count || 0
  const softBarData = [
    { name: 'Communication', score: softSkills.communication },
    { name: 'Leadership', score: softSkills.leadership },
    { name: 'Problem Solving', score: softSkills.problemSolving },
  ]

  return (
    <div className="min-h-screen bg-dark-bg py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 animate-fadeIn flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold mb-2">Analytics Dashboard</h1>
            <p className="text-lg text-dark-text/70">
              System performance and candidate statistics
            </p>
          </div>
          <button
            type="button"
            onClick={() => fetchData({ showLoader: false })}
            disabled={refreshing}
            className={`btn-primary flex items-center gap-2 ${refreshing ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            {refreshing ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaServer className="w-4 h-4" />}
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-950/30 border border-red-700/50 text-red-400 px-4 py-3 rounded-lg mb-8">
            {error}
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="card glass-effect">
            <p className="text-sm text-dark-text/60 mb-2">Total Resumes</p>
            <p className="text-3xl font-bold text-primary">
              {stats?.total_resumes || 0}
            </p>
          </div>
          <div className="card glass-effect">
            <p className="text-sm text-dark-text/60 mb-2">Total Chunks</p>
            <p className="text-3xl font-bold text-secondary">
              {stats?.total_chunks || 0}
            </p>
          </div>
          <div className="card glass-effect">
            <div className="flex items-center space-x-2">
              <FaServer className="text-primary w-4 h-4" />
              <p className="text-sm text-dark-text/60">System Status</p>
            </div>
            <p className="text-2xl font-bold text-green-400 mt-2">
              {health?.status === 'healthy' ? 'Healthy' : 'Degraded'}
            </p>
          </div>
          <div className="card glass-effect">
            <div className="flex items-center space-x-2">
              <FaDatabase className="text-secondary w-4 h-4" />
              <p className="text-sm text-dark-text/60">Vector Store</p>
            </div>
            <p className="text-2xl font-bold text-blue-400 mt-2">
              {health?.services?.matching?.vector_store_ready ? 'Ready' : 'Loading'}
            </p>
          </div>
        </div>

        {/* AI Performance Metrics */}
        <div className="card glass-effect mb-8">
          <h2 className="text-xl font-bold mb-4">AI Performance Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
              <p className="text-sm text-dark-text/60 mb-1">Avg Execution Time</p>
              <p className="text-2xl font-bold text-primary">{baselineExecutionTime}</p>
              <p className="text-xs text-dark-text/50 mt-1">Baseline</p>
            </div>
            <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
              <p className="text-sm text-dark-text/60 mb-1">Avg Tokens / Query</p>
              <p className="text-2xl font-bold text-secondary">{avgTokensPerQuery}</p>
            </div>
            <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
              <p className="text-sm text-dark-text/60 mb-1">Est. Cost / Query</p>
              <p className="text-2xl font-bold text-green-400">${estimatedCostPerQuery}</p>
            </div>
            <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
              <p className="text-sm text-dark-text/60 mb-1">Total Queries</p>
              <p className="text-2xl font-bold text-blue-400">{localMetrics.queriesProcessed}</p>
              <p className="text-xs text-dark-text/50 mt-1">Stored in localStorage</p>
            </div>
          </div>
        </div>

        {/* Bias Detection Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="card glass-effect">
            <h2 className="text-xl font-bold mb-4">Bias Detection Stats</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
                <p className="text-sm text-dark-text/60 mb-1">Bias Free Queries</p>
                <p className="text-2xl font-bold text-green-400">{biasFreePct}%</p>
              </div>
              <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
                <p className="text-sm text-dark-text/60 mb-1">Biased Queries</p>
                <p className="text-2xl font-bold text-red-400">{biasedCount}</p>
              </div>
              <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
                <p className="text-sm text-dark-text/60 mb-1">Clean Queries</p>
                <p className="text-2xl font-bold text-primary">{cleanCount}</p>
              </div>
            </div>

            {total === 0 ? (
              <div className="text-sm text-dark-text/60">
                No bias data yet. Run a few matches to populate local bias stats.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={biasPieData}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label
                  >
                    {biasPieData.map((_, index) => (
                      <Cell key={`bias-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#f1f5f9' }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Soft Skills Distribution */}
          <div className="card glass-effect">
            <h2 className="text-xl font-bold mb-4">Soft Skills Distribution</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
                <p className="text-sm text-dark-text/60 mb-1">Avg Communication</p>
                <p className="text-2xl font-bold text-primary">
                  {softCount ? softSkills.communication : 0}
                </p>
              </div>
              <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
                <p className="text-sm text-dark-text/60 mb-1">Avg Leadership</p>
                <p className="text-2xl font-bold text-secondary">
                  {softCount ? softSkills.leadership : 0}
                </p>
              </div>
              <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
                <p className="text-sm text-dark-text/60 mb-1">Avg Problem Solving</p>
                <p className="text-2xl font-bold text-green-400">
                  {softCount ? softSkills.problemSolving : 0}
                </p>
              </div>
            </div>

            {softCount === 0 ? (
              <div className="text-sm text-dark-text/60">
                No soft skills data yet. Run matches (with soft skills enabled) to populate this chart.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={softBarData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#f1f5f9' }}
                  />
                  <Bar dataKey="score" fill="#7c3aed" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* System Health */}
        <div className="card glass-effect mb-8">
          <h2 className="text-xl font-bold mb-4">System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
              <p className="text-sm text-dark-text/60 mb-1">Gateway</p>
              <div className="flex items-center gap-2">
                <span className={statusDot(health?.status === 'healthy')} />
                <p className="text-lg font-bold">{health?.status || 'unknown'}</p>
              </div>
              <p className="text-xs text-dark-text/50 mt-1">http://localhost:8000/health</p>
            </div>
            <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
              <p className="text-sm text-dark-text/60 mb-1">Matching Service</p>
              <div className="flex items-center gap-2">
                <span className={statusDot(health?.services?.matching?.status === 'healthy')} />
                <p className="text-lg font-bold">{health?.services?.matching?.status || 'unknown'}</p>
              </div>
              <p className="text-xs text-dark-text/50 mt-1">via http://localhost:8000/health</p>
            </div>
            <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
              <p className="text-sm text-dark-text/60 mb-1">Vector Store Docs</p>
              <p className="text-2xl font-bold text-blue-400">
                {health?.services?.matching?.total_documents || 0}
              </p>
            </div>
            <div className="bg-dark-surface/50 border border-dark-border rounded-lg p-4">
              <p className="text-sm text-dark-text/60 mb-1">Vector Store Ready</p>
              <div className="flex items-center gap-2">
                <span className={statusDot(Boolean(health?.services?.matching?.vector_store_ready))} />
                <p className="text-lg font-bold">
                  {health?.services?.matching?.vector_store_ready ? 'Ready' : 'Not Ready'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Categories Distribution */}
          {stats?.categories && stats.categories.length > 0 && (
            <div className="card glass-effect">
              <h2 className="text-xl font-bold mb-6">Candidates by Category</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={stats.categories}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                  >
                    {stats.categories.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#f1f5f9' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-4 pt-4 border-t border-dark-border">
                <div className="space-y-2">
                  {stats.categories.slice(0, 5).map((cat, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-dark-text/70">{cat.name}</span>
                      <span className="font-semibold">{cat.count} ({cat.percentage}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Experience Levels */}
          {stats?.experience_levels && stats.experience_levels.length > 0 && (
            <div className="card glass-effect">
              <h2 className="text-xl font-bold mb-6">Candidates by Experience Level</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={stats.experience_levels}
                  margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#f1f5f9' }}
                  />
                  <Bar dataKey="count" fill="#7c3aed" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-4 pt-4 border-t border-dark-border">
                <div className="space-y-2">
                  {stats.experience_levels.map((level, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-dark-text/70">{level.name}</span>
                      <span className="font-semibold">{level.count} ({level.percentage}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Role Categories */}
        {stats?.role_categories && stats.role_categories.length > 0 && (
          <div className="card glass-effect">
            <h2 className="text-xl font-bold mb-6">Candidates by Role Category</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={stats.role_categories}
                margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="name"
                  stroke="#94a3b8"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-6 pt-6 border-t border-dark-border grid grid-cols-2 md:grid-cols-4 gap-4">
              {stats.role_categories.slice(0, 4).map((role, index) => (
                <div key={index}>
                  <p className="text-xs text-dark-text/60">{role.name}</p>
                  <p className="text-lg font-bold text-primary">{role.count}</p>
                  <p className="text-xs text-dark-text/50">{role.percentage}%</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Service Health Details */}
        {health && (
          <div className="card glass-effect mt-8">
            <h2 className="text-xl font-bold mb-4">Service Health Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-dark-text/60 mb-1">Gateway Status</p>
                <p className={`font-semibold ${health.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'}`}>
                  {health.status}
                </p>
              </div>
              <div>
                <p className="text-sm text-dark-text/60 mb-1">Last Updated</p>
                <p className="font-semibold text-blue-400">
                  {new Date(health.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
            {health.services?.matching && (
              <div className="mt-4 pt-4 border-t border-dark-border">
                <h3 className="font-semibold mb-3">Matching Service</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-dark-text/70">Status</span>
                    <span className={`font-semibold ${health.services.matching.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'}`}>
                      {health.services.matching.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-text/70">Documents</span>
                    <span className="font-semibold">{health.services.matching.total_documents}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Analytics
