import React, { createContext, useState } from 'react'

export const ResultsContext = createContext()

export function ResultsProvider({ children }) {
  const [results, setResults] = useState(null)

  return (
    <ResultsContext.Provider value={{ results, setResults }}>
      {children}
    </ResultsContext.Provider>
  )
}
