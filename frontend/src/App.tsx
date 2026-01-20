import './App.css'
import MicRecorder from './component/MicRecorder'
import MatchResult from './component/MatchResult'
import { useState } from 'react'

function App() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any[]>([]) // store final matches

  function pingForResult(task_id: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`http://localhost:8000/task_status/${task_id}`)
          const data = await response.json()

          if (data.status !== "pending") {
            clearInterval(interval)
            resolve(data)
          }
        } catch (err) {
          clearInterval(interval)
          reject(err)
        }
      }, 2000)
    })
  }

  async function uploadAudio(wavBlob: Blob) {
    setLoading(true)
    setResults([]) // clear previous results

    const formData = new FormData()
    formData.append("file", wavBlob, "mic.wav")

    const response = await fetch("http://localhost:8000/match_file", {
      method: "POST",
      body: formData,
    })

    const result = await response.json()
    console.log("Task ID:", result.task_id)

    try {
      const finalResult = await pingForResult(result.task_id)
      console.log("Match result:", finalResult)
      setResults(finalResult.result || [])
      return finalResult
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: "20px", maxWidth: "600px", margin: "0 auto" }}>
      <h1>Spectra</h1>
      <MicRecorder onRecordingComplete={uploadAudio} />
      {loading && <p>Matching audio… please wait.</p>}
      <MatchResult results={results} />
    </div>
  )
}

export default App
