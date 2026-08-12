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

    try {
      const response = await fetch('https://myfinancialbot.decodgo.com/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
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

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // keep the possibly-incomplete last line for next chunk

        for (const line of lines) {
          if (!line.trim()) continue
          const event = JSON.parse(line)

          if (event.type === 'delta') {
            appendToBot(event.text)
          } else if (event.type === 'done') {
            setMessages(prev => prev.map(m => (
              m.id === botId ? { ...m, sources: event.sources || [] } : m
            )))
          }
        }
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now().toString(),
        type: 'error',
        content: `Error: ${error.message}. Please try again.`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
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
