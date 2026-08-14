import React, { useState } from 'react'
import { parseImage, parseImages, exportData, exportAggregate } from './api'
import CameraCapture from './CameraCapture'

export default function App() {
  const [files, setFiles] = useState([])
  const [documentType, setDocumentType] = useState('id')
  const [provider, setProvider] = useState('azure')
  const [results, setResults] = useState([]) // parsed results list
  const [editableList, setEditableList] = useState([])
  const [loading, setLoading] = useState(false)
  const [cameraOpen, setCameraOpen] = useState(false)

  async function onParse(e) {
    if (!files || files.length === 0) return
    setLoading(true)
    const res = await parseImages(files, documentType, provider)
    // res is array of {filename, data}
    setResults(res)
    setEditableList(res.map(r => r.data))
    setLoading(false)
  }

  async function onExport(format, index=null) {
    if (index === null){
      // aggregate export all edited
      await exportAggregate(editableList, format === 'word' ? 'word' : 'excel')
    } else {
      const item = editableList[index]
      await exportData(item, format === 'word' ? 'word' : 'excel')
    }
  }

  return (
    <div className="container">
      <h1>قراءة البطاقات</h1>
      <div className="controls">
        <input type="file" accept="image/*" multiple onChange={e => setFiles(Array.from(e.target.files))} />
        <button onClick={() => setCameraOpen(true)}>استخدام الكاميرا</button>
        <select value={documentType} onChange={e => setDocumentType(e.target.value)}>
          <option value="id">هوية</option>
          <option value="license">رخصة قيادة</option>
          <option value="vehicle">استمارة سيارة</option>
          <option value="residency">إقامة</option>
        </select>
        <select value={provider} onChange={e => setProvider(e.target.value)}>
          <option value="azure">Azure OCR</option>
          <option value="local">Tesseract (محلي)</option>
        </select>
        <button onClick={onParse} disabled={loading}>{loading ? 'جارٍ...' : 'اقرأ'}</button>
      </div>

      {cameraOpen && (
        <CameraCapture onCapture={(file) => { setFiles([file]); setCameraOpen(false); setTimeout(() => onParse(), 200) }} onClose={() => setCameraOpen(false)} />
      )}

      {results && results.length > 0 && (
        <div className="result">
          <h2>مراجعة وتحرير النتائج ({results.length})</h2>
          {results.map((r, idx) => (
            <div key={idx} style={{border:'1px solid #ddd',padding:8,marginBottom:8}}>
              <div style={{fontWeight:700}}>{r.filename}</div>
              {Object.keys(editableList[idx] || {}).map(key => (
                <div key={key} style={{marginBottom:6}}>
                  <label style={{display:'block',fontWeight:600}}>{key}</label>
                  <input value={(editableList[idx] && editableList[idx][key]) || ''} onChange={e => {
                    const newList = editableList.slice()
                    newList[idx] = {...newList[idx], [key]: e.target.value}
                    setEditableList(newList)
                  }} style={{width:'100%'}} />
                </div>
              ))}
              <div style={{marginTop:6}}>
                <button onClick={() => onExport('word', idx)}>حفظ Word</button>
                <button onClick={() => onExport('excel', idx)}>حفظ Excel</button>
              </div>
            </div>
          ))}
          <div style={{marginTop:12}}>
            <button onClick={() => onExport('excel', null)}>تصدير جميع النتائج إلى Excel</button>
            <button onClick={() => onExport('word', null)}>تصدير جميع النتائج إلى Word (ZIP)</button>
          </div>
        </div>
      )}
    </div>
  )
}
