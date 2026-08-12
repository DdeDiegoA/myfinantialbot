import React, { useState } from 'react'
import { motion } from 'framer-motion'
import MessageList from './MessageList'
import InputBox from './InputBox'

const headerVariants = {
  initial: { y: -20, opacity: 0 },
  animate: {
    y: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15,
      delay: 0.1,
    },
  },
}

function ChatInterface({ messages, loading, onSendMessage, messagesEndRef }) {
  const [expandedSource, setExpandedSource] = useState(null)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <motion.header
        className="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm"
        variants={headerVariants}
        initial="initial"
        animate="animate"
      >
        <div className="max-w-4xl mx-auto px-4 py-4">
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <motion.div
              className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg flex items-center justify-center text-white font-bold text-sm"
              whileHover={{ scale: 1.1, rotate: 5 }}
              whileTap={{ scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 200 }}
            >
              M
            </motion.div>
            <h1 className="text-2xl font-bold text-slate-900">MyFinancialBot</h1>
          </motion.div>
          <motion.p
            className="text-sm text-slate-600 mt-1"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            DIAN Tax Law & Colombian Financial Regulations Assistant
          </motion.p>
        </div>
      </motion.header>

      {/* Messages Area */}
      <motion.div
        className="flex-1 overflow-y-auto"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15 }}
      >
        <div className="max-w-4xl mx-auto">
          <MessageList 
            messages={messages}
            loading={loading}
            expandedSource={expandedSource}
            onSourceClick={setExpandedSource}
          />
          <div ref={messagesEndRef} />
        </div>
      </motion.div>

      {/* Input Area */}
      <motion.div
        className="sticky bottom-0 bg-white border-t border-slate-200 shadow-lg"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{
          type: 'spring',
          stiffness: 100,
          damping: 15,
          delay: 0.25,
        }}
      >
        <div className="max-w-4xl mx-auto px-4 py-4">
          <InputBox 
            onSendMessage={onSendMessage}
            disabled={loading}
          />
          <motion.p
            className="text-xs text-slate-500 text-center mt-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
          >
            MyFinancialBot can make mistakes. Verify important information with official DIAN sources.
          </motion.p>
        </div>
      </motion.div>
    </div>
  )
}

export default ChatInterface
