import React, { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import ChatInterface from './components/ChatInterface'

function App() {
  const [messages, setMessages] = useState([
    {
      id: '1',
      type: 'system',
      content: 'Welcome to MyFinancialBot. I can help you with questions about Colombian tax law and DIAN regulations.',
      timestamp: new Date(),
    }
  ])
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (question) => {
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: question,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setLoading(true)

    const botId = `${Date.now()}-bot`
    let botMessageStarted = false

    // Inactivity deadline, not a total one: a real answer can take ~20s to
    // its first token and then stream for a while, so a flat timeout would
    // abort valid slow answers. This only fires when the server has sent
    // nothing at all for STALL_MS -- the case where the UI would otherwise
    // sit on a spinner forever (reader.read() blocks with no timeout of its
    // own, and setLoading(false) never runs while it's blocked).
    const STALL_MS = 45000
    const controller = new AbortController()
    let stallTimer = setTimeout(() => controller.abort(), STALL_MS)
    const resetStallTimer = () => {
      clearTimeout(stallTimer)
      stallTimer = setTimeout(() => controller.abort(), STALL_MS)
    }

    const apiUrl = import.meta.env.PROD
      ? 'https://myfinancialbot.decodgo.com/ask/stream'
      : 'http://localhost:8000/ask/stream'

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      })

      if (!response.ok || !response.body) {
        throw new Error(`API error: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const appendToBot = (text) => {
        if (!botMessageStarted) {
          botMessageStarted = true
          setLoading(false)
          setMessages(prev => [...prev, {
            id: botId,
            type: 'bot',
            content: text,
            sources: [],
            timestamp: new Date(),
          }])
        } else {
          setMessages(prev => prev.map(m => (
            m.id === botId ? { ...m, content: m.content + text } : m
          )))
        }
      }

      let sawDone = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        resetStallTimer()

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // keep the possibly-incomplete last line for next chunk

        for (const line of lines) {
          if (!line.trim()) continue
          const event = JSON.parse(line)

          if (event.type === 'delta') {
            appendToBot(event.text)
          } else if (event.type === 'replace') {
            // Server retracted everything streamed so far (leaked model
            // reasoning that resolved to a refusal, or a mid-stream crash).
            // Overwrite rather than append so the discarded text never shows.
            if (!botMessageStarted) {
              appendToBot(event.text)
            } else {
              setMessages(prev => prev.map(m => (
                m.id === botId ? { ...m, content: event.text, sources: [] } : m
              )))
            }
          } else if (event.type === 'done') {
            sawDone = true
            setMessages(prev => prev.map(m => (
              m.id === botId ? { ...m, sources: event.sources || [] } : m
            )))
          }
        }
      }

      // Stream ended without a `done` event: the connection dropped mid-answer
      // rather than finishing. Text already shown stays, but say it's partial
      // instead of presenting a truncated answer as complete.
      if (!sawDone && botMessageStarted) {
        setMessages(prev => prev.map(m => (
          m.id === botId
            ? { ...m, content: `${m.content}\n\n_(respuesta incompleta — la conexión se interrumpió)_` }
            : m
        )))
      }
    } catch (error) {
      // An abort surfaces as a DOMException whose raw message ("signal is
      // aborted without reason") means nothing to a user -- name the actual
      // situation instead.
      const content = error.name === 'AbortError'
        ? 'El servidor no respondió a tiempo. Intenta de nuevo.'
        : `Error: ${error.message}. Intenta de nuevo.`
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'error',
        content,
        timestamp: new Date(),
      }])
    } finally {
      clearTimeout(stallTimer)
      setLoading(false)
    }
  }

  return (
    <motion.div
      className="flex flex-col h-screen bg-bg"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <ChatInterface 
        messages={messages}
        loading={loading}
        onSendMessage={handleSendMessage}
        messagesEndRef={messagesEndRef}
      />
    </motion.div>
  )
}

export default App
