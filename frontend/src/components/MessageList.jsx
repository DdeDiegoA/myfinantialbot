import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Message from './Message'

const loadingDotVariants = {
  initial: { y: 0 },
  animate: {
    y: [-4, 0, -4],
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
}

function MessageList({ messages, loading, expandedSource, onSourceClick }) {
  return (
    <div className="space-y-5 px-6 py-6">
      <AnimatePresence mode="popLayout">
        {messages.map((message) => (
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
            className="flex gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            <div className="w-6 h-6 rounded-md bg-accent flex items-center justify-center text-accent-ink text-xs font-semibold flex-shrink-0">
              M
            </div>
            <div className="flex gap-1.5 items-center py-2">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-1.5 h-1.5 bg-ink-faint rounded-full"
                  variants={loadingDotVariants}
                  initial="initial"
                  animate="animate"
                  transition={{ delay: i * 0.15 }}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default MessageList
