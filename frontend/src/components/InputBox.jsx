import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'

function InputBox({ onSendMessage, disabled }) {
  const [input, setInput] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const textareaRef = useRef(null)

  const handleChange = (e) => {
    setInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const height = Math.min(textareaRef.current.scrollHeight, 200)
      textareaRef.current.style.height = `${height}px`
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !disabled) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input.trim())
      setInput('')
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
    }
  }

  return (
    <div className="flex gap-2 items-end">
      <motion.textarea
        ref={textareaRef}
        value={input}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder="Pregunta sobre impuestos, RUT, facturación..."
        disabled={disabled}
        className="flex-1 resize-none rounded-xl bg-surface border px-3.5 py-2.5 text-sm text-ink focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
        style={{ maxHeight: '200px', minHeight: '42px' }}
        animate={{ borderColor: isFocused ? 'oklch(0.65 0.16 255)' : 'oklch(0.30 0.016 258)' }}
        transition={{ duration: 0.15 }}
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        className="rounded-xl px-4 h-[42px] text-sm flex-shrink-0 disabled:cursor-not-allowed"
        style={{
          backgroundColor: disabled || !input.trim() ? 'oklch(0.245 0.015 258)' : 'oklch(0.48 0.16 255)',
          color: disabled || !input.trim() ? 'oklch(0.60 0.012 258)' : 'oklch(0.99 0 0)',
        }}
      >
        Enviar
      </button>
    </div>
  )
}

export default InputBox
