import { useState } from 'react'
import './CVUploader.css'

const CVUploader = ({ onResults, onError, onLoading }) => {
  const [jobDescription, setJobDescription] = useState(null)
  const [cvs, setCvs] = useState([])
  const [progress, setProgress] = useState(0)
  const [processingStatus, setProcessingStatus] = useState('')

  const handleJobDescriptionChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      setJobDescription(file)
    } else {
      onError('Job description must be a PDF file')
    }
  }

  const handleCVsChange = (e) => {
    const files = Array.from(e.target.files)
    const validFiles = files.filter(file => 
      file.type === 'application/pdf' || 
      file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    
    if (validFiles.length !== files.length) {
      onError('Some files were ignored. Only PDF and DOCX files are accepted.')
    }
    
    setCvs(validFiles)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!jobDescription) {
      onError('Please upload a job description file')
      return
    }
    
    if (cvs.length === 0) {
      onError('Please upload at least one CV')
      return
    }

    const formData = new FormData()
    formData.append('job_description', jobDescription)
    cvs.forEach(cv => {
      formData.append('cvs[]', cv)
    })

    try {
      onLoading(true)
      setProgress(0)
      setProcessingStatus('Starting analysis...')

      const response = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))
            
            if (data.progress !== undefined) {
              setProgress(data.progress)
              setProcessingStatus(`Processing CV ${data.current} of ${data.total}...`)
            }
            
            if (data.results) {
              onResults(data.results)
              setProcessingStatus('Analysis complete!')
            }
          }
        }
      }
    } catch (error) {
      onError(error.message)
      setProcessingStatus('')
    } finally {
      onLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <div className="form-group">
        <label htmlFor="jobDescription">
          Job Description (PDF):
          <input
            type="file"
            id="jobDescription"
            accept="application/pdf"
            onChange={handleJobDescriptionChange}
            required
          />
        </label>
        {jobDescription && (
          <span className="file-name">{jobDescription.name}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="cvs">
          CVs (PDF or DOCX):
          <input
            type="file"
            id="cvs"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleCVsChange}
            multiple
            required
          />
        </label>
        {cvs.length > 0 && (
          <div className="file-list">
            <p>Selected files ({cvs.length}):</p>
            <ul>
              {cvs.map((file, index) => (
                <li key={index}>{file.name}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <button type="submit" className="submit-button">
        Analyze CVs
      </button>

      {processingStatus && (
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="progress-status">{processingStatus}</p>
        </div>
      )}
    </form>
  )
}

export default CVUploader 