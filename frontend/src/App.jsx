import { useState } from 'react'
import CVUploader from './components/CVUploader'
import AnalysisResults from './components/AnalysisResults'
import './App.css'

function App() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedCandidate, setSelectedCandidate] = useState(null)

  const handleResults = (data) => {
    setResults(data)
    setLoading(false)
    setError(null)
    setSelectedCandidate(null) // Reset selected candidate when new results arrive
  }

  const handleError = (errorMessage) => {
    setError(errorMessage)
    setLoading(false)
  }

  const handleLoading = (isLoading) => {
    setLoading(isLoading)
    if (isLoading) {
      setError(null)
      setSelectedCandidate(null) // Reset selected candidate when loading starts
    }
  }

  const handleCandidateSelect = (candidateId) => {
    setSelectedCandidate(candidateId === selectedCandidate ? null : candidateId)
  }

  return (
    <div className="app">
      <header>
        <h1>CV Analysis Tool</h1>
      </header>
      
      <main className={selectedCandidate ? 'with-details' : ''}>
        <section className="upload-section">
          <CVUploader 
            onResults={handleResults}
            onError={handleError}
            onLoading={handleLoading}
          />
          
          {loading && (
            <div className="loader">
              <div className="spinner"></div>
              <p>Analyzing CVs...</p>
            </div>
          )}

          {error && (
            <div className="error">
              <p>Error: {error}</p>
            </div>
          )}
        </section>

        <section className="results-section">
          {results.length > 0 && !loading && (
            <AnalysisResults 
              results={results} 
              selectedCandidate={selectedCandidate}
              onCandidateSelect={handleCandidateSelect}
            />
          )}
        </section>

        {selectedCandidate && (
          <section className={`details-section ${selectedCandidate ? 'visible' : ''}`}>
            <div className="details-header">
              <h2>Candidate Details</h2>
              <button 
                className="close-details-btn"
                onClick={() => setSelectedCandidate(null)}
              >
                ×
              </button>
            </div>
            {results.find(r => r.participant_id === selectedCandidate) && (
              <div className="candidate-details">
                {results.find(r => r.participant_id === selectedCandidate)?.reasons.map((reason, index) => (
                  <div key={index} className="reason-item">
                    <div className="reason-header">
                      <span className="reason-number">{index + 1}</span>
                    </div>
                    <p>{reason}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  )
}

export default App
