import React, { useContext, useLayoutEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FaStar,
  FaCheckCircle,
  FaTimesCircle,
  FaArrowLeft,
  FaFilter,
} from 'react-icons/fa'
import { ResultsContext } from '../context/ResultsContext'

function Results() {
  const navigate = useNavigate()
  const { results } = useContext(ResultsContext) || {}
  const [filterType, setFilterType] = useState('all')

  // Ensure the default view shows ALL candidates whenever new results arrive.
  // This prevents a previously-selected filter (e.g. "high") from hiding results
  // on the next match request while staying on the same route.
  useLayoutEffect(() => {
    setFilterType('all')
  }, [results])

  if (!results) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-dark-text/70 mb-4">No results available</p>
          <button
            onClick={() => navigate('/match')}
            className="btn-primary flex items-center space-x-2"
          >
            <FaArrowLeft />
            <span>Back to Search</span>
          </button>
        </div>
      </div>
    )
  }

  const candidates = results.candidates || []
  const parsedJob = results.parsed_job || {}

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getScoreBgColor = (score) => {
    if (score >= 80) return 'bg-green-950/30 border-green-700/50'
    if (score >= 60) return 'bg-yellow-950/30 border-yellow-700/50'
    return 'bg-red-950/30 border-red-700/50'
  }

  const filteredCandidates = candidates.filter((candidate) => {
    if (filterType === 'all') return true
    if (filterType === 'high') return candidate.final_score >= 80
    if (filterType === 'medium') return candidate.final_score >= 60 && candidate.final_score < 80
    if (filterType === 'low') return candidate.final_score < 60
    return true
  })

  return (
    <div className="min-h-screen bg-dark-bg py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 animate-fadeIn">
          <button
            onClick={() => navigate('/match')}
            className="flex items-center space-x-2 text-primary hover:text-secondary transition-colors mb-6"
          >
            <FaArrowLeft />
            <span>Back to Search</span>
          </button>

          <h1 className="text-4xl font-bold mb-4">Candidate Matches</h1>
          <p className="text-lg text-dark-text/70">
            Found {candidates.length} qualified candidates
          </p>
        </div>

        {/* Job Summary Card */}
        <div className="card glass-effect mb-8">
          <h2 className="text-2xl font-bold mb-4">Job Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-dark-text/60">Role</p>
              <p className="font-semibold text-primary">{parsedJob.role_category}</p>
            </div>
            <div>
              <p className="text-sm text-dark-text/60">Level</p>
              <p className="font-semibold text-primary">{parsedJob.experience_level}</p>
            </div>
            <div>
              <p className="text-sm text-dark-text/60">Required Skills</p>
              <p className="font-semibold">{parsedJob.required_skills?.length || 0}</p>
            </div>
            <div>
              <p className="text-sm text-dark-text/60">Execution Time</p>
              <p className="font-semibold text-secondary">
                {results.execution_time?.toFixed(2)}s
              </p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-dark-border">
            <p className="text-sm text-dark-text/60 mb-2">Required Skills:</p>
            <div className="flex flex-wrap gap-2">
              {parsedJob.required_skills?.slice(0, 10).map((skill, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm"
                >
                  {skill}
                </span>
              ))}
              {parsedJob.required_skills?.length > 10 && (
                <span className="px-3 py-1 bg-dark-surface border border-dark-border rounded-full text-sm">
                  +{parsedJob.required_skills.length - 10} more
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="mb-8 animate-fadeIn">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-950/25 border border-green-700/40 rounded-xl px-5 py-4">
              <p className="text-xs text-green-200/80 mb-1">Candidates per second</p>
              <p className="text-2xl font-bold text-green-200">
                {results.performance?.candidates_per_second ?? '\u2014'}
              </p>
            </div>
            <div className="bg-green-950/25 border border-green-700/40 rounded-xl px-5 py-4">
              <p className="text-xs text-green-200/80 mb-1">Total candidates found</p>
              <p className="text-2xl font-bold text-green-200">
                {results.performance?.total_candidates ?? '\u2014'}
              </p>
            </div>
            <div className="bg-green-950/25 border border-green-700/40 rounded-xl px-5 py-4">
              <p className="text-xs text-green-200/80 mb-1">Execution time</p>
              <p className="text-2xl font-bold text-green-200">
                {results.performance?.execution_time_seconds ?? '\u2014'}s
              </p>
            </div>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
          <div className="flex items-center space-x-2">
            <FaFilter className="text-primary" />
            <span className="font-semibold">Filter by Score:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              { value: 'all', label: 'All' },
              { value: 'high', label: 'High (80+)' },
              { value: 'medium', label: 'Medium (60-79)' },
              { value: 'low', label: 'Low (<60)' },
            ].map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setFilterType(value)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  filterType === value
                    ? 'bg-gradient-dark text-white'
                    : 'bg-dark-surface border border-dark-border text-dark-text hover:border-primary'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Candidates List */}
        <div className="space-y-4">
          {filteredCandidates.length === 0 ? (
            <div className="card glass-effect text-center py-12">
              <p className="text-dark-text/70">No candidates match the selected filter</p>
            </div>
          ) : (
            filteredCandidates.map((candidate, index) => (
              <div key={index} className="card glass-effect hover:border-primary/50 animate-fadeIn">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  {/* Candidate Info */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <p className="text-sm text-dark-text/60">Resume ID: {candidate.resume_id}</p>
                        <p className="text-lg font-bold">
                          Rank #{candidate.rank}
                        </p>
                      </div>
                      <div className={`border rounded-lg px-3 py-1 ${getScoreBgColor(candidate.final_score)}`}>
                        <p className={`text-2xl font-bold ${getScoreColor(candidate.final_score)}`}>
                          {candidate.final_score}
                        </p>
                        <p className="text-xs text-dark-text/70">Final Score</p>
                      </div>
                    </div>

                    {/* Experience Info */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                      <div>
                        <p className="text-xs text-dark-text/60">Experience Level</p>
                        <p className="font-semibold text-sm">{candidate.experience_level}</p>
                      </div>
                      <div>
                        <p className="text-xs text-dark-text/60">Role Category</p>
                        <p className="font-semibold text-sm">{candidate.role_category}</p>
                      </div>
                      <div>
                        <p className="text-xs text-dark-text/60">Semantic Score</p>
                        <p className="font-semibold text-sm text-secondary">
                          {candidate.semantic_score}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-dark-text/60">Skill Coverage</p>
                        <p className="font-semibold text-sm text-primary">
                          {candidate.skill_coverage}%
                        </p>
                      </div>
                    </div>

                    {/* Why this candidate? */}
                    <div
                      className="mb-4 bg-blue-950/25 border border-blue-700/40 text-blue-100 px-4 py-3 rounded-lg"
                      role="note"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-lg leading-none" aria-hidden="true">
                          {'\u2139\uFE0F'}
                        </span>
                        <p className="font-semibold text-sm">Why this candidate?</p>
                      </div>
                      <p className="text-sm text-blue-100/90 leading-relaxed whitespace-pre-line">
                        {candidate.explanation ||
                          `This ${candidate.experience_level} ${candidate.role_category} professional matches ${candidate.skill_coverage}% of required skills. Strong in: ${(candidate.matched_skills || []).slice(0, 2).join(', ')}. Missing: ${(candidate.missing_skills || []).slice(0, 2).join(', ')}. Overall: ${candidate.final_score > 70 ? 'Strong' : candidate.final_score > 50 ? 'Moderate' : 'Partial'} match.`}
                      </p>
                    </div>

                    {/* Skills */}
                    <div className="mb-3">
                      <p className="text-xs text-dark-text/60 mb-2">Matched Skills:</p>
                      <div className="flex flex-wrap gap-2">
                        {candidate.matched_skills?.slice(0, 5).map((skill, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-green-950/30 text-green-400 rounded text-xs flex items-center space-x-1"
                          >
                            <FaCheckCircle className="w-3 h-3" />
                            <span>{skill}</span>
                          </span>
                        ))}
                        {candidate.matched_skills?.length > 5 && (
                          <span className="px-2 py-1 bg-dark-surface border border-dark-border rounded text-xs">
                            +{candidate.matched_skills.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Missing Skills */}
                    {candidate.missing_skills && candidate.missing_skills.length > 0 && (
                      <div>
                        <p className="text-xs text-dark-text/60 mb-2">Missing Skills:</p>
                        <div className="flex flex-wrap gap-2">
                          {candidate.missing_skills.slice(0, 3).map((skill, i) => (
                            <span
                              key={i}
                              className="px-2 py-1 bg-red-950/30 text-red-400 rounded text-xs flex items-center space-x-1"
                            >
                              <FaTimesCircle className="w-3 h-3" />
                              <span>{skill}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default Results
