const DEFAULT_BACKEND = localStorage.getItem('backendUrl') || 'http://localhost:8000'

function getBaseUrl(){
  return localStorage.getItem('backendUrl') || DEFAULT_BACKEND
}

export async function parseImage(file, documentType='id', provider='azure', saveLog=false){
  const form = new FormData()
  form.append('file', file)
  form.append('document_type', documentType)
  form.append('provider', provider)
  form.append('save_log', saveLog ? 'true' : 'false')
  const resp = await fetch(getBaseUrl() + '/parse', { method: 'POST', body: form })
  if (!resp.ok) throw new Error('Parse failed')
  return resp.json()
}

export async function getLogs(){
  const resp = await fetch(getBaseUrl() + '/logs')
  if (!resp.ok) throw new Error('failed')
  return resp.json()
}

export async function getLog(name){
  const resp = await fetch(getBaseUrl() + '/logs/' + encodeURIComponent(name))
  if (!resp.ok) throw new Error('failed')
  const ct = resp.headers.get('content-type') || ''
  if (ct.startsWith('application/json')) return resp.json()
  // otherwise return image url
  return getBaseUrl() + '/logs/' + encodeURIComponent(name)
}

export async function parseImages(files, documentType='id', provider='azure'){
  const results = []
  for (const f of files){
    const r = await parseImage(f, documentType, provider)
    results.push(r)
  }
  return results
}

export async function enhanceImage(file){
  // simple client-side contrast enhancement using canvas
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const c = document.createElement('canvas')
      c.width = img.naturalWidth
      c.height = img.naturalHeight
      const ctx = c.getContext('2d')
      ctx.drawImage(img, 0, 0)
      try{
        const imgd = ctx.getImageData(0,0,c.width,c.height)
        const data = imgd.data
        const contrast = 30 // -255..255
        const factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
        for (let i=0;i<data.length;i+=4){
          data[i] = truncate(factor*(data[i]-128)+128)
          data[i+1] = truncate(factor*(data[i+1]-128)+128)
          data[i+2] = truncate(factor*(data[i+2]-128)+128)
        }
        ctx.putImageData(imgd,0,0)
        c.toBlob(b => {
          const f = new File([b], file.name.replace(/(\.\w+)?$/, '_enh$1'), { type: 'image/jpeg' })
          resolve(f)
        }, 'image/jpeg', 0.9)
      }catch(e){
        // fallback return original
        resolve(file)
      }
    }
    img.onerror = () => reject(new Error('image load error'))
    img.src = URL.createObjectURL(file)
  })
}

function truncate(v){
  return v < 0 ? 0 : v > 255 ? 255 : v
}

export async function exportData(data, format='word'){
  const resp = await fetch('http://localhost:8000/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data, format })
  })
  if (!resp.ok) throw new Error('Export failed')
  const blob = await resp.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  // try to get filename from content-disposition
  const cd = resp.headers.get('content-disposition')
  let filename = 'export.' + (format === 'word' ? 'docx' : 'xlsx')
  if (cd) {
    const m = /filename="?([^\";]+)"?/.exec(cd)
    if (m) filename = m[1]
  }
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export async function exportAggregate(rows, format='excel'){
  const resp = await fetch('http://localhost:8000/export/aggregate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: rows, format })
  })
  if (!resp.ok) throw new Error('Export failed')
  const blob = await resp.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const cd = resp.headers.get('content-disposition')
  let filename = 'export.' + (format === 'word' ? 'zip' : 'xlsx')
  if (cd) {
    const m = /filename="?([^\";]+)"?/.exec(cd)
    if (m) filename = m[1]
  }
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}
