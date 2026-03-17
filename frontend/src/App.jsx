import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ResultsProvider } from './context/ResultsContext'
import Navigation from './components/Navigation'
import Home from './pages/Home'
import Match from './pages/Match'
import Results from './pages/Results'
import Analytics from './pages/Analytics'

function App() {
  return (
    <ResultsProvider>
      <Router>
        <div className="min-h-screen bg-dark-bg text-dark-text">
          <Navigation />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/match" element={<Match />} />
            <Route path="/results" element={<Results />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </div>
      </Router>
    </ResultsProvider>
  )
}

export default App
