import React, { useState, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import { FaSearch, FaSpinner, FaCode, FaChartBar, FaPaintBrush } from 'react-icons/fa'
import axios from 'axios'
import { apiService } from '../utils/api'
import { ResultsContext } from '../context/ResultsContext'

function Match() {
  const [jobDescription, setJobDescription] = useState('')
  const [topK, setTopK] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { setResults } = useContext(ResultsContext) || {}

  // Example job descriptions
  const examples = [
    {
      title: 'HR Manager',
      icon: FaChartBar,
      description:
        'We are looking for an experienced HR manager with strong skills in recruitment, employee relations, performance management, and HR policy development. The candidate should have experience with HRIS systems, payroll processing, onboarding, and compensation and benefits administration.',
    },
    {
      title: 'Data Scientist',
      icon: FaPaintBrush,
      description:
        'We need a data scientist with experience in machine learning, Python, TensorFlow, and data analysis. Strong skills in statistical modeling, pandas, numpy, and experience working with large datasets and data visualization is required.',
    },
    {
      title: 'Backend Developer',
      icon: FaPaintBrush,
      description:
        'We are looking for a senior backend developer with strong experience in Python, REST APIs, Docker, and PostgreSQL. The candidate should have experience building scalable microservices and cloud deployment.',
    },
    {
      title: 'Implicit HR',
      icon: FaChartBar,
      description:
        'We need someone who manages employee-related processes, supports workplace policies, handles hiring activities, and ensures smooth organizational operations.',
    },
  ]

  // Count words in text
  const countWords = (text) => {
    return text
      .trim()
      .split(/\s+/)
      .filter((word) => word.length > 0).length
  }

  const wordCount = countWords(jobDescription)
  const isValidDescription = wordCount >= 20
  const WARNING_ICON = '\u26A0\uFE0F'

  const safeJsonParse = (value, fallback) => {
    try {
      if (!value) return fallback
      return JSON.parse(value)
    } catch {
      return fallback
    }
  }

  const persistAnalyticsMetrics = (matchResponse) => {
    try {
      // Total queries processed
      const queryCountKey = 'rms_queries_processed'
      const currentCount = parseInt(localStorage.getItem(queryCountKey) || '0', 10) || 0
      localStorage.setItem(queryCountKey, String(currentCount + 1))

      // Bias detection stats
      const biasKey = 'rms_bias_stats'
      const biasStats = safeJsonParse(localStorage.getItem(biasKey), {
        total: 0,
        clean: 0,
        biased: 0,
        types: { age: 0, gender: 0, language: 0 },
      })

      const biasCheck = matchResponse?.bias_check
      biasStats.total += 1
      if (biasCheck?.has_bias) {
        biasStats.biased += 1
        const types = Array.isArray(biasCheck.bias_types) ? biasCheck.bias_types : []
        if (types.some((t) => String(t).includes('age'))) biasStats.types.age += 1
        if (types.some((t) => String(t).includes('gender'))) biasStats.types.gender += 1
        if (types.some((t) => String(t).includes('cultural') || String(t).includes('language')))
          biasStats.types.language += 1
      } else {
        biasStats.clean += 1
      }
      localStorage.setItem(biasKey, JSON.stringify(biasStats))

      // Soft skills stats (top candidate only)
      const softKey = 'rms_soft_skills_stats'
      const softStats = safeJsonParse(localStorage.getItem(softKey), {
        count: 0,
        communication_total: 0,
        leadership_total: 0,
        problem_solving_total: 0,
      })

      const soft = matchResponse?.candidates?.[0]?.soft_skills_assessment
      if (soft && typeof soft === 'object') {
        const communication = Number(soft.communication_score)
        const leadership = Number(soft.leadership_score)
        const problemSolving = Number(soft.problem_solving_score)

        if (Number.isFinite(communication) && Number.isFinite(leadership) && Number.isFinite(problemSolving)) {
          softStats.count += 1
          softStats.communication_total += communication
          softStats.leadership_total += leadership
          softStats.problem_solving_total += problemSolving
          localStorage.setItem(softKey, JSON.stringify(softStats))
        }
      }
    } catch (e) {
      console.warn('Failed to persist analytics metrics:', e)
    }
  }

  const persistQueryTrends = (matchResponse) => {
    try {
      const key = 'rms_query_history'
      const existing = safeJsonParse(localStorage.getItem(key), [])
      const history = Array.isArray(existing) ? existing : []

      const parsedJob = matchResponse?.parsed_job || {}
      const requiredSkills = Array.isArray(parsedJob?.required_skills) ? parsedJob.required_skills : []
      const roleCategory = String(parsedJob?.role_category || '').trim()
      const experienceLevel = String(parsedJob?.experience_level || '').trim()

      history.push({
        ts: new Date().toISOString(),
        role_category: roleCategory,
        experience_level: experienceLevel,
        required_skills: requiredSkills,
      })

      localStorage.setItem(key, JSON.stringify(history.slice(-50)))
    } catch (e) {
      console.warn('Failed to persist query trends:', e)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!isValidDescription) {
      setError(`${WARNING_ICON} Please enter a job description with at least 20 words. Current: ${wordCount} words`)
      return
    }

    setLoading(true)

    try {
      const data = await apiService.matchJob(jobDescription, topK)

      const totalFound = Number.isFinite(Number(data?.total_found))
        ? Number(data.total_found)
        : Array.isArray(data?.candidates)
          ? data.candidates.length
          : 0

      if (totalFound === 0) {
        setError('No candidates found. Try a different job description.')
        return
      }

      persistAnalyticsMetrics(data)
      persistQueryTrends(data)

      const softSkillsData = data.candidates
        .filter((c) => c.soft_skills_assessment)
        .map((c) => c.soft_skills_assessment)

      if (softSkillsData.length > 0) {
        const existing = JSON.parse(localStorage.getItem('softSkillsData') || '[]')
        const updated = [...existing, ...softSkillsData]
        localStorage.setItem('softSkillsData', JSON.stringify(updated))
      }

      if (setResults) {
        setResults(data)
      }
      navigate('/results')
    } catch (err) {
      if (err.response?.status === 400) {
        setError('\u26A0\uFE0F Invalid Job Description: Please enter a real job description with role requirements and skills.')
        return
      }

      const status = axios.isAxiosError(err) ? err.response?.status : undefined

      if (status === 503) {
        setError(`${WARNING_ICON} Service Unavailable: Please try again in a moment.`)
      } else {
        setError(`${WARNING_ICON} Something went wrong. Please try again.`)
      }
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleExampleClick = (exampleText) => {
    setJobDescription(exampleText)
    setError('')
  }

  return (
    <div className="min-h-screen bg-dark-bg py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12 animate-fadeIn">
          <h1 className="text-4xl md:text-5xl font-extrabold mb-4">
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Find Candidates
            </span>
          </h1>
          <p className="text-lg text-dark-text/70 max-w-2xl mx-auto">
            Paste your job description and let our AI find the best matching candidates from our database of 38,000+ resumes
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="card glass-effect">
              <div className="space-y-6">
                {/* Job Description Input */}
                <div>
                  <label htmlFor="jobDescription" className="block text-sm font-semibold mb-3">
                    Job Description <span className="text-primary">*</span>
                  </label>
                  <textarea
                    id="jobDescription"
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste your complete job description here. Include title, responsibilities, required skills, qualifications, and nice-to-have skills..."
                    className="input-field min-h-56 resize-none"
                    disabled={loading}
                  />
                  <div className="mt-2 flex justify-between items-center">
                    <p className="text-sm text-dark-text/60">
                      {wordCount} words
                      {wordCount < 20 && (
                        <span className="text-yellow-600 ml-2">
                          Minimum 20 words required ({20 - wordCount} more needed)
                        </span>
                      )}
                      {wordCount >= 20 && (
                        <span className="text-green-600 ml-2">
                          {'\u2713'} Ready to match
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {/* Top K Selection */}
                <div>
                  <label htmlFor="topK" className="block text-sm font-semibold mb-3">
                    Number of Candidates to Return
                  </label>
                  <div className="flex items-center space-x-4">
                    <input
                      type="range"
                      id="topK"
                      min="1"
                      max="20"
                      value={topK}
                      onChange={(e) => setTopK(parseInt(e.target.value))}
                      className="flex-1 h-2 bg-dark-bg rounded-lg appearance-none cursor-pointer accent-primary"
                      disabled={loading}
                    />
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        min="1"
                        max="20"
                        value={topK}
                        onChange={(e) => {
                          const val = parseInt(e.target.value)
                          if (val >= 1 && val <= 20) {
                            setTopK(val)
                          }
                        }}
                        className="input-field w-16 text-center"
                        disabled={loading}
                      />
                      <span className="text-dark-text/70">/ 20</span>
                    </div>
                  </div>
                  <p className="mt-2 text-xs text-dark-text/60">
                    Select how many top matching candidates you want to see from our database
                  </p>
                </div>

                {/* Error Message (prominent, above submit) */}
                {error && (
                  <div
                    role="alert"
                    className="animate-fadeIn bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg flex items-start gap-3 shadow-sm transition-opacity duration-200"
                  >
                    <p className="flex-1 text-sm md:text-base font-medium leading-relaxed">{error}</p>
                    <button
                      type="button"
                      onClick={() => setError('')}
                      className="ml-2 text-red-700/70 hover:text-red-800 transition-colors leading-none"
                      aria-label="Dismiss error"
                    >
                      X
                    </button>
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={loading || !isValidDescription}
                  className={`btn-primary w-full flex items-center justify-center space-x-2 transition-all ${
                    loading || !isValidDescription ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {loading ? (
                    <>
                      <FaSpinner className="animate-spin" />
                      <span>Processing... This may take a moment</span>
                    </>
                  ) : (
                    <>
                      <FaSearch />
                      <span>Find Matching Candidates</span>
                    </>
                  )}
                </button>

                <p className="text-xs text-dark-text/50 text-center">
                  Tip: Use one of the example job descriptions below to test the system quickly
                </p>
              </div>
            </form>
          </div>

          {/* Examples Sidebar */}
          <div className="lg:col-span-1">
            <h2 className="text-xl font-bold mb-4">Example Job Descriptions</h2>
            <div className="space-y-3">
              {examples.map((example, index) => {
                const Icon = example.icon
                return (
                  <button
                    key={index}
                    onClick={() => handleExampleClick(example.description)}
                    disabled={loading}
                    className="card group w-full text-left hover:border-primary/30 hover:bg-dark-surface transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="flex items-start space-x-3">
                      <div className="w-10 h-10 rounded-lg bg-gradient-dark flex items-center justify-center flex-shrink-0">
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm group-hover:text-primary transition-colors">
                          {example.title}
                        </h3>
                        <p className="text-xs text-dark-text/60 mt-1 truncate">
                          Click to fill the textarea
                        </p>
                      </div>
                      <span className="text-primary opacity-0 group-hover:opacity-100 transition-opacity text-lg">
                        {'\u2192'}
                      </span>
                    </div>
                  </button>
                )
              })}
            </div>

            {/* Info Box */}
            <div className="card glass-effect mt-6 bg-secondary/10 border-secondary/30">
              <h3 className="font-semibold text-sm mb-2 text-secondary">
                {'\uD83D\uDCA1'} Pro Tips
              </h3>
              <ul className="text-xs text-dark-text/70 space-y-1.5">
                <li>{'\u2022'} Be specific about requirements</li>
                <li>{'\u2022'} Include expected experience level</li>
                <li>{'\u2022'} Mention important tools/frameworks</li>
                <li>{'\u2022'} Describe key responsibilities</li>
                <li>{'\u2022'} Note nice-to-have skills</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card text-center">
            <FaSearch className="w-8 h-8 text-primary mx-auto mb-3" />
            <h3 className="font-semibold mb-2">Semantic Search</h3>
            <p className="text-sm text-dark-text/70">
              Our AI understands the meaning and context of your job description, not just keywords
            </p>
          </div>
          <div className="card text-center">
            <FaChartBar className="w-8 h-8 text-secondary mx-auto mb-3" />
            <h3 className="font-semibold mb-2">Ranked Results</h3>
            <p className="text-sm text-dark-text/70">
              Candidates are ranked by relevance with detailed scores and explanations
            </p>
          </div>
          <div className="card text-center">
            <FaCode className="w-8 h-8 text-primary mx-auto mb-3" />
            <h3 className="font-semibold mb-2">Instant Results</h3>
            <p className="text-sm text-dark-text/70">
              Get results in less than a second from our 38,000+ candidate database
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Match
