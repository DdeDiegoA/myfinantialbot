import React, { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

function InputBox({ onSendMessage, disabled }) {
  const [input, setInput] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const [rows, setRows] = useState(1)
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
      setRows(1)
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  return (
    <motion.div
      className="flex gap-3 items-end"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 15, delay: 0.2 }}
    >
      <motion.textarea
        ref={textareaRef}
        value={input}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder="Ask about Colombian tax law, DIAN regulations, or financial compliance..."
        disabled={disabled}
        className="flex-1 resize-none rounded-lg border border-slate-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:bg-slate-100 disabled:text-slate-500 disabled:cursor-not-allowed transition-all"
        style={{ maxHeight: '200px', minHeight: '44px' }}
        animate={{
          borderColor: isFocused ? 'rgb(59, 130, 246)' : 'rgb(203, 213, 225)',
          boxShadow: isFocused
            ? '0 0 0 3px rgba(59, 130, 246, 0.1)'
            : '0 0 0 0px rgba(59, 130, 246, 0)',
        }}
        transition={{ type: 'spring', stiffness: 200 }}
      />
      <motion.button
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        className="bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg px-6 py-3 transition-all disabled:bg-slate-400 disabled:cursor-not-allowed flex items-center gap-2 h-11 flex-shrink-0 shadow-md hover:shadow-lg"
        whileHover={!disabled && input.trim() ? { scale: 1.05 } : {}}
        whileTap={!disabled && input.trim() ? { scale: 0.95 } : {}}
        animate={{
          backgroundColor:
            disabled || !input.trim() ? 'rgb(148, 163, 184)' : 'rgb(37, 99, 235)',
        }}
        transition={{ type: 'spring', stiffness: 200 }}
      >
        <span>Send</span>
        <motion.span
          className="text-lg"
          animate={{ x: [0, 3, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          →
        </motion.span>
      </motion.button>
    </motion.div>
  )
}

export default InputBox
