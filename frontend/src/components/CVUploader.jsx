import { useState } from 'react'

const CVUploader = ({ onResults, onError, onLoading }) => {
  const [jobDescription, setJobDescription] = useState(null)
  const [cvs, setCvs] = useState([])

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
      const response = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      onResults(data)
    } catch (error) {
      onError(error.message)
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
    </form>
  )
}

export default CVUploader 