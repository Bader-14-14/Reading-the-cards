import React, { useState } from 'react'
import CameraCapture from './CameraCapture'

export default function App(){
  const [files, setFiles] = useState([])
  const [cameraOpen, setCameraOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  async function onParse(){
    if (!files || files.length === 0) return
    setLoading(true)
    // placeholder: in next step we'll call the backend
    console.log('Would parse files:', files.map(f => f.name || 'file'))
    setLoading(false)
  }

  function handleCapture(file){
    setFiles([file])
    setCameraOpen(false)
    setTimeout(() => onParse(), 200)
  }

  return (
    <div className="container">
      <h1>قراءة البطاقات</h1>
      <div>
        <input type="file" accept="image/*" multiple onChange={e => setFiles(Array.from(e.target.files))} />
        <button onClick={() => setCameraOpen(true)}>استخدام الكاميرا</button>
        <button onClick={onParse} disabled={loading}>{loading ? 'جارٍ...' : 'اقرأ'}</button>
      </div>
      {cameraOpen && <CameraCapture onCapture={handleCapture} onClose={() => setCameraOpen(false)} />}
      {files && files.length > 0 && (
        <div style={{marginTop:12}}>
          <h3>ملفات جاهزة:</h3>
          <ul>{files.map((f, i) => <li key={i}>{f.name || 'capture'}</li>)}</ul>
        </div>
      )}
    </div>
  )
}
