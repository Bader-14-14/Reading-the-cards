export async function parseImage(file, documentType='id', provider='azure'){
  const form = new FormData()
  form.append('file', file)
  form.append('document_type', documentType)
  form.append('provider', provider)
  const resp = await fetch('http://localhost:8000/parse', { method: 'POST', body: form })
  if (!resp.ok) throw new Error('Parse failed')
  return resp.json()
}

export async function parseImages(files, documentType='id', provider='azure'){
  const results = []
  for (const f of files){
    const r = await parseImage(f, documentType, provider)
    results.push(r)
  }
  return results
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
