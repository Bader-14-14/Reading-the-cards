import React, { useEffect, useState } from 'react'
import { getLogs, getLog } from './api'

export default function Logs(){
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(null)
  const [content, setContent] = useState(null)

  useEffect(()=>{
    async function load(){
      const res = await getLogs()
      setItems(res.logs || [])
    }
    load()
  },[])

  async function open(name){
    setSelected(name)
    const res = await getLog(name)
    setContent(res)
  }

  return (
    <div>
      <h2>سجلات الصور والنتائج</h2>
      <div style={{display:'flex',gap:12}}>
        <div style={{width:240,borderRight:'1px solid #ddd',paddingRight:8}}>
          <ul>
            {items.map(i => (
              <li key={i}><button style={{width:'100%',textAlign:'left'}} onClick={() => open(i)}>{i}</button></li>
            ))}
          </ul>
        </div>
        <div style={{flex:1}}>
          {selected ? (
            <div>
              <h3>{selected}</h3>
              {typeof content === 'string' ? (
                <img src={`http://localhost:8000/logs/${selected}`} alt={selected} style={{maxWidth:'100%'}} />
              ) : (
                <pre>{JSON.stringify(content, null, 2)}</pre>
              )}
            </div>
          ) : <div>اختر سجل لعرضه</div>}
        </div>
      </div>
    </div>
  )
}
