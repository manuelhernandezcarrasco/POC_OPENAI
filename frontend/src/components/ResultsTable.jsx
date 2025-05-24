const ResultsTable = ({ results }) => {
  return (
    <div className="results-table">
      <h2>Analysis Results</h2>
      <table>
        <thead>
          <tr>
            <th>Participant ID</th>
            <th>Score</th>
            <th>Reasons</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result, index) => (
            <tr key={result.participant_id || index}>
              <td>{result.participant_id}</td>
              <td className="score-cell">
                <div className="score-bar">
                  <div 
                    className="score-fill"
                    style={{ width: `${result.score}%` }}
                  />
                  <span>{result.score}</span>
                </div>
              </td>
              <td>
                <ul className="reasons-list">
                  {result.reasons.map((reason, idx) => (
                    <li key={idx}>{reason}</li>
                  ))}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ResultsTable 