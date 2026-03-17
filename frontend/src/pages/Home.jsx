import React from 'react'
import { Link } from 'react-router-dom'
import {
  FaRobot,
  FaChartLine,
  FaLightbulb,
  FaArrowRight,
  FaSearch,
  FaAward,
  FaDatabase,
  FaCheckCircle,
  FaGithub,
  FaTwitter,
  FaLinkedin,
} from 'react-icons/fa'

function Home() {
  const features = [
    {
      icon: FaSearch,
      title: 'Semantic Search',
      description: 'Understands meaning and context, not just keywords. Finds candidates based on semantic relevance.',
    },
    {
      icon: FaAward,
      title: 'AI Ranking',
      description: 'Scores candidates with detailed explanations combining semantic relevance and skill overlap.',
    },
    {
      icon: FaDatabase,
      title: '38,000+ Resumes',
      description: 'Pre-indexed and ready to search. Continuously expanded with new candidate data.',
    },
  ]

  const steps = [
    {
      number: '1',
      title: 'Enter Job Description',
      description: 'Paste your complete job description including requirements, responsibilities, and desired skills.',
      icon: FaLightbulb,
    },
    {
      number: '2',
      title: 'AI Analyzes & Matches',
      description: 'Our AI engine analyzes the job and performs semantic matching across the candidate pool.',
      icon: FaRobot,
    },
    {
      number: '3',
      title: 'Get Ranked Candidates',
      description: 'Receive a ranked list of qualified candidates with scores, skills, and detailed explanations.',
      icon: FaChartLine,
    },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-dark-bg">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary opacity-10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary opacity-10 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
          <div className="text-center animate-fadeIn">
            <div className="flex items-center justify-center gap-2 mb-6">
              <div className="w-10 h-10 bg-gradient-dark rounded-lg flex items-center justify-center">
                <FaRobot className="text-white w-6 h-6" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                ResumeAI
              </span>
            </div>

            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Find the Perfect Candidate with AI
            </h1>
            <p className="text-xl text-dark-text/80 mb-8 max-w-2xl mx-auto">
              Semantic search and intelligent matching. Discover top-qualified candidates in seconds,
              powered by advanced AI and machine learning.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link to="/match" className="btn-primary flex items-center justify-center">
                Start Matching <FaArrowRight className="ml-2" />
              </Link>
              <Link to="/analytics" className="btn-secondary flex items-center justify-center">
                View Analytics
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Why Choose ResumeAI?</h2>
          <p className="text-dark-text/70 max-w-2xl mx-auto">
            Leverage cutting-edge AI technology to find your ideal candidates faster and smarter.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="card group hover:shadow-lg hover:shadow-primary/20 hover:-translate-y-1 transition-all duration-300"
              >
                <div className="w-14 h-14 bg-gradient-dark rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-dark-text/70">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-dark-surface/50 py-20 border-t border-dark-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">How It Works</h2>
          <p className="text-dark-text/70 text-center max-w-2xl mx-auto mb-12">
            Three simple steps to find your perfect candidates.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-4">
            {steps.map((step, index) => {
              const Icon = step.icon
              return (
                <div key={index} className="relative">
                  {/* Card */}
                  <div className="card text-center group">
                    {/* Step Number */}
                    <div className="flex justify-center mb-6">
                      <div className="w-16 h-16 bg-gradient-dark rounded-full flex items-center justify-center">
                        <span className="text-2xl font-bold text-white">{step.number}</span>
                      </div>
                    </div>

                    {/* Icon */}
                    <Icon className="w-8 h-8 text-primary mx-auto mb-4" />

                    <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                    <p className="text-dark-text/70">{step.description}</p>
                  </div>

                  {/* Arrow between steps */}
                  {index < steps.length - 1 && (
                    <div className="hidden md:flex absolute -right-4 top-1/3 translate-x-12">
                      <FaArrowRight className="w-6 h-6 text-primary/50" />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative bg-gradient-dark my-12">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-white rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to revolutionize your hiring?
          </h2>
          <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto">
            Post a job description and discover your ideal candidates in minutes, not weeks.
          </p>
          <Link
            to="/match"
            className="inline-flex items-center px-8 py-3 bg-dark-surface text-primary rounded-lg font-semibold hover:bg-dark-surface/80 hover:shadow-lg hover:shadow-primary/30 transition-all"
          >
            Start Finding Candidates <FaArrowRight className="ml-2" />
          </Link>
        </div>
      </div>

      {/* Stats Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
          <div className="card group hover:shadow-lg hover:shadow-secondary/20">
            <FaDatabase className="w-8 h-8 text-secondary mx-auto mb-3" />
            <div className="text-4xl font-bold text-primary mb-2">38K+</div>
            <p className="text-dark-text/70">Candidates Indexed</p>
          </div>
          <div className="card group hover:shadow-lg hover:shadow-primary/20">
            <FaLightbulb className="w-8 h-8 text-primary mx-auto mb-3" />
            <div className="text-4xl font-bold text-secondary mb-2">AI-Powered</div>
            <p className="text-dark-text/70">Semantic Matching</p>
          </div>
          <div className="card group hover:shadow-lg hover:shadow-secondary/20">
            <FaCheckCircle className="w-8 h-8 text-primary mx-auto mb-3" />
            <div className="text-4xl font-bold text-primary mb-2">&lt; 1s</div>
            <p className="text-dark-text/70">Response Time</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-auto bg-dark-surface border-t border-dark-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            {/* Brand */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 bg-gradient-dark rounded-lg flex items-center justify-center">
                  <FaRobot className="text-white w-6 h-6" />
                </div>
                <span className="text-xl font-bold text-primary">ResumeAI</span>
              </div>
              <p className="text-dark-text/70 text-sm">
                AI-powered resume matching system for intelligent candidate discovery.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2">
                <li>
                  <Link to="/match" className="text-dark-text/70 hover:text-primary transition-colors">
                    Find Candidates
                  </Link>
                </li>
                <li>
                  <Link to="/analytics" className="text-dark-text/70 hover:text-primary transition-colors">
                    Analytics
                  </Link>
                </li>
                <li>
                  <a href="http://localhost:8000/docs" className="text-dark-text/70 hover:text-primary transition-colors">
                    API Docs
                  </a>
                </li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#" className="text-dark-text/70 hover:text-primary transition-colors">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="text-dark-text/70 hover:text-primary transition-colors">
                    GitHub
                  </a>
                </li>
                <li>
                  <a href="#" className="text-dark-text/70 hover:text-primary transition-colors">
                    Changelog
                  </a>
                </li>
              </ul>
            </div>

            {/* Social */}
            <div>
              <h4 className="font-semibold mb-4">Follow Us</h4>
              <div className="flex gap-4">
                <a
                  href="#"
                  className="w-10 h-10 bg-dark-bg rounded-lg flex items-center justify-center text-dark-text/70 hover:text-primary hover:bg-primary/10 transition-colors"
                >
                  <FaGithub className="w-5 h-5" />
                </a>
                <a
                  href="#"
                  className="w-10 h-10 bg-dark-bg rounded-lg flex items-center justify-center text-dark-text/70 hover:text-primary hover:bg-primary/10 transition-colors"
                >
                  <FaTwitter className="w-5 h-5" />
                </a>
                <a
                  href="#"
                  className="w-10 h-10 bg-dark-bg rounded-lg flex items-center justify-center text-dark-text/70 hover:text-primary hover:bg-primary/10 transition-colors"
                >
                  <FaLinkedin className="w-5 h-5" />
                </a>
              </div>
            </div>
          </div>

          {/* Bottom */}
          <div className="border-t border-dark-border pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-dark-text/60 text-sm">
                © 2024 ResumeAI. All rights reserved.
              </p>
              <div className="flex gap-6 mt-4 md:mt-0">
                <a href="#" className="text-dark-text/60 hover:text-primary text-sm transition-colors">
                  Privacy Policy
                </a>
                <a href="#" className="text-dark-text/60 hover:text-primary text-sm transition-colors">
                  Terms of Service
                </a>
                <a href="#" className="text-dark-text/60 hover:text-primary text-sm transition-colors">
                  Contact
                </a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Home
