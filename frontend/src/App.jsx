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

    try {
      const response = await fetch('https://myfinancialbot.decodgo.com/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      const botMessage = {
        id: Date.now().toString(),
        type: 'bot',
        content: data.answer,
        sources: data.sources || [],
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, botMessage])
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
