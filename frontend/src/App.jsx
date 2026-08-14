import React, { useState } from 'react'
import { parseImage, exportData } from './api'

export default function App() {
  const [file, setFile] = useState(null)
  const [documentType, setDocumentType] = useState('id')
  const [provider, setProvider] = useState('azure')
  const [result, setResult] = useState(null)
  const [editable, setEditable] = useState(null)
  const [loading, setLoading] = useState(false)

  async function onParse(e) {
    if (!file) return
    setLoading(true)
    const res = await parseImage(file, documentType, provider)
    setResult(res)
    setEditable(res.data)
    setLoading(false)
  }

  async function onExport(format) {
    if (!editable) return
    await exportData(editable, format)
  }

  return (
    <div className="container">
      <h1>قراءة البطاقات</h1>
      <div className="controls">
        <input type="file" accept="image/*" onChange={e => setFile(e.target.files[0])} />
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

      {result && editable && (
        <div className="result">
          <h2>مراجعة وتحرير الحقول</h2>
          <div className="fields">
            {Object.keys(editable).map(key => (
              <div key={key} style={{marginBottom:8}}>
                <label style={{display:'block',fontWeight:600}}>{key}</label>
                <input value={editable[key] || ''} onChange={e => setEditable({...editable, [key]: e.target.value})} style={{width:'100%'}} />
              </div>
            ))}
          </div>
          <div className="exports">
            <button onClick={() => onExport('word')}>حفظ Word</button>
            <button onClick={() => onExport('excel')}>حفظ Excel</button>
          </div>
        </div>
      )}
    </div>
  )
}
