import { useState } from 'react';
import './AnalysisResults.css';

const AnalysisResults = ({ results, selectedCandidate, onCandidateSelect }) => {
  const [sortConfig, setSortConfig] = useState({ key: 'score', direction: 'desc' });

  const sortedResults = [...results].sort((a, b) => {
    if (sortConfig.key === 'score') {
      return sortConfig.direction === 'asc' 
        ? a.score - b.score 
        : b.score - a.score;
    }
    return 0;
  });

  const handleSort = (key) => {
    setSortConfig({
      key,
      direction: sortConfig.key === key && sortConfig.direction === 'desc' ? 'asc' : 'desc'
    });
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#2ecc71';
    if (score >= 60) return '#f1c40f';
    return '#e74c3c';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excellent Match';
    if (score >= 60) return 'Good Match';
    return 'Needs Review';
  };

  return (
    <div className="analysis-results">
      <div className="results-header">
        <h2>CV Analysis Results</h2>
        <div className="results-summary">
          <div className="summary-card">
            <h3>Total Candidates</h3>
            <p>{results.length}</p>
          </div>
          <div className="summary-card">
            <h3>Average Score</h3>
            <p>{Math.round(results.reduce((acc, curr) => acc + curr.score, 0) / results.length)}</p>
          </div>
          <div className="summary-card">
            <h3>Top Score</h3>
            <p>{Math.max(...results.map(r => r.score))}</p>
          </div>
        </div>
      </div>

      <div className="results-content">
        <div className="candidates-list">
          <table>
            <thead>
              <tr>
                <th>Candidate</th>
                <th onClick={() => handleSort('score')} className="sortable">
                  Score {sortConfig.key === 'score' && (sortConfig.direction === 'desc' ? '↓' : '↑')}
                </th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedResults.map((result) => (
                <tr 
                  key={result.participant_id}
                  className={selectedCandidate === result.participant_id ? 'selected' : ''}
                >
                  <td>
                    <div className="candidate-info">
                      <span className="candidate-name">{result.candidate_name}</span>
                      <span className="candidate-id">ID: {result.participant_id}</span>
                    </div>
                  </td>
                  <td>
                    <div className="score-bar">
                      <div 
                        className="score-fill"
                        style={{ 
                          width: `${result.score}%`,
                          backgroundColor: getScoreColor(result.score)
                        }}
                      />
                      <span>{result.score}</span>
                    </div>
                  </td>
                  <td>
                    <span className="status-badge" style={{ backgroundColor: getScoreColor(result.score) }}>
                      {getScoreLabel(result.score)}
                    </span>
                  </td>
                  <td>
                    <button 
                      onClick={() => onCandidateSelect(result.participant_id)}
                      className={`view-details-btn ${selectedCandidate === result.participant_id ? 'active' : ''}`}
                    >
                      {selectedCandidate === result.participant_id ? 'Hide Details' : 'View Details'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalysisResults; 