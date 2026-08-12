import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Message from './Message'

const loadingDotVariants = {
  initial: { y: 0 },
  animate: {
    y: [-8, 0, -8],
    transition: {
      duration: 1.2,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
}

function MessageList({ messages, loading, expandedSource, onSourceClick }) {
  const containerVariants = {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  }

  return (
    <motion.div
      className="space-y-4 px-4 py-6"
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      <AnimatePresence mode="popLayout">
        {messages.map((message, idx) => (
          <Message
            key={message.id}
            message={message}
            isExpanded={expandedSource === message.id}
            onSourceClick={onSourceClick}
          />
        ))}
      </AnimatePresence>

      <AnimatePresence>
        {loading && (
          <motion.div
            className="flex gap-3 mb-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ type: 'spring', stiffness: 100, damping: 15 }}
          >
            <motion.div
              className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              M
            </motion.div>
            <motion.div
              className="bg-slate-100 rounded-lg p-4 max-w-2xl flex gap-2 items-center"
              animate={{ boxShadow: ['0 0 0 rgba(59, 130, 246, 0)', '0 0 8px rgba(59, 130, 246, 0.3)', '0 0 0 rgba(59, 130, 246, 0)'] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-2 h-2 bg-blue-600 rounded-full"
                  variants={loadingDotVariants}
                  initial="initial"
                  animate="animate"
                  transition={{ delay: i * 0.15 }}
                />
              ))}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default MessageList
