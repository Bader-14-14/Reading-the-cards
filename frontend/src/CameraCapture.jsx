import React, { useRef, useEffect, useState } from 'react'

export default function CameraCapture({ onCapture, onClose }){
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const [stream, setStream] = useState(null)

  useEffect(() => {
    async function start(){
      try{
        const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false })
        setStream(s)
        if (videoRef.current) videoRef.current.srcObject = s
      }catch(e){
        console.error('camera error', e)
      }
    }
    start()
    return () => {
      if (stream){
        stream.getTracks().forEach(t => t.stop())
      }
    }
  }, [])

  const capture = () => {
    const v = videoRef.current
    const c = canvasRef.current
    if (!v || !c) return
    c.width = v.videoWidth
    c.height = v.videoHeight
    const ctx = c.getContext('2d')
    ctx.drawImage(v, 0, 0, c.width, c.height)
    c.toBlob(b => {
      const file = new File([b], `capture_${Date.now()}.jpg`, { type: 'image/jpeg' })
      onCapture(file)
    }, 'image/jpeg', 0.9)
  }

  return (
    <div className="camera-modal">
      <div className="camera-container">
        <video ref={videoRef} autoPlay playsInline muted style={{width:'100%',maxHeight: '60vh',objectFit:'contain'}} />
        <canvas ref={canvasRef} style={{display:'none'}} />
        <div style={{display:'flex',gap:8,marginTop:8}}>
          <button onClick={capture}>التقاط</button>
          <button onClick={onClose}>إغلاق</button>
        </div>
      </div>
    </div>
  )
}
