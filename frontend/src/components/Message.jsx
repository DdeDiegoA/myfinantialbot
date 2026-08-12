import React from 'react'
import { motion } from 'framer-motion'

const messageVariants = {
  initial: (isUser) => ({
    opacity: 0,
    y: 20,
    x: isUser ? 20 : -20,
  }),
  animate: {
    opacity: 1,
    y: 0,
    x: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15,
      duration: 0.4,
    },
  },
  exit: (isUser) => ({
    opacity: 0,
    y: -20,
    x: isUser ? 20 : -20,
    transition: { duration: 0.2 },
  }),
}

const sourceVariants = {
  initial: { opacity: 0, height: 0 },
  animate: {
    opacity: 1,
    height: 'auto',
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
  exit: { opacity: 0, height: 0, transition: { duration: 0.2 } },
}

function Message({ message, isExpanded, onSourceClick }) {
  const isUser = message.type === 'user'
  const isSystem = message.type === 'system'
  const isError = message.type === 'error'

  if (isSystem) {
    return (
      <motion.div
        className="flex justify-center"
        variants={messageVariants}
        custom={isUser}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <div className="bg-blue-50 text-blue-800 px-4 py-3 rounded-lg text-sm border border-blue-200 max-w-2xl">
          {message.content}
        </div>
      </motion.div>
    )
  }

  if (isError) {
    return (
      <motion.div
        className="flex gap-3"
        variants={messageVariants}
        custom={isUser}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 text-sm flex-shrink-0">
          !
        </div>
        <div className="bg-red-50 rounded-lg p-4 max-w-2xl border border-red-200">
          <p className="text-red-800 text-sm">{message.content}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}
      variants={messageVariants}
      custom={isUser}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {!isUser && (
        <motion.div
          className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 15 }}
        >
          M
        </motion.div>
      )}
      <div className={`flex-1 ${isUser ? 'flex justify-end' : ''}`}>
        <motion.div
          className={`rounded-lg p-4 max-w-2xl shadow-lg hover:shadow-xl transition-shadow ${
            isUser 
              ? 'bg-blue-600 text-white' 
              : 'bg-slate-100 text-slate-900'
          }`}
          whileHover={{ y: -2 }}
        >
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
          
          {!isUser && message.sources && message.sources.length > 0 && (
            <motion.div
              className="mt-4 pt-4 border-t border-slate-300"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <motion.button
                onClick={() => onSourceClick(isExpanded ? null : message.id)}
                className="text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors flex items-center gap-2"
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
              >
                <span>📚 {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}</span>
                <motion.span
                  animate={{ rotate: isExpanded ? 180 : 0 }}
                  transition={{ type: 'spring', stiffness: 200 }}
                >
                  ▶
                </motion.span>
              </motion.button>
              
              <motion.div
                variants={sourceVariants}
                initial="initial"
                animate={isExpanded ? 'animate' : 'initial'}
                exit="exit"
                className="overflow-hidden"
              >
                {isExpanded && (
                  <div className="mt-3 space-y-2">
                    {message.sources.map((source, idx) => (
                      <motion.div
                        key={idx}
                        className="text-xs bg-slate-200 rounded p-2"
                        initial={{ opacity: 0, y: -8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05 }}
                      >
                        <div className="font-semibold text-slate-900 truncate">
                          {source.source_file || source.source_url || 'Unknown source'}
                        </div>
                        <p className="text-slate-700 mt-1 line-clamp-2">{source.chunk_text}</p>
                        {source.source_url && (
                          <a 
                            href={source.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline mt-1 inline-block"
                          >
                            View source →
                          </a>
                        )}
                      </motion.div>
                    ))}
                  </div>
                )}
              </motion.div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </motion.div>
  )
}

export default Message
