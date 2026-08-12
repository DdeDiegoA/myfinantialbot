import React from 'react'
import { motion } from 'framer-motion'

const messageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.2, ease: [0.16, 1, 0.3, 1] },
  },
  exit: { opacity: 0, transition: { duration: 0.15 } },
}

const sourceVariants = {
  initial: { opacity: 0, height: 0 },
  animate: { opacity: 1, height: 'auto', transition: { duration: 0.2, ease: [0.16, 1, 0.3, 1] } },
  exit: { opacity: 0, height: 0, transition: { duration: 0.15 } },
}

const Message = React.forwardRef(function Message({ message, isExpanded, onSourceClick }, ref) {
  const isUser = message.type === 'user'
  const isSystem = message.type === 'system'
  const isError = message.type === 'error'

  if (isSystem) {
    return (
      <motion.div ref={ref} className="flex justify-center" variants={messageVariants} initial="initial" animate="animate" exit="exit">
        <p className="text-sm text-ink-muted text-center max-w-md">{message.content}</p>
      </motion.div>
    )
  }

  if (isError) {
    return (
      <motion.div ref={ref} variants={messageVariants} initial="initial" animate="animate" exit="exit">
        <div className="bg-danger-bg rounded-lg px-4 py-3">
          <p className="text-sm text-danger">{message.content}</p>
        </div>
      </motion.div>
    )
  }

  if (isUser) {
    return (
      <motion.div ref={ref} className="flex justify-end" variants={messageVariants} initial="initial" animate="animate" exit="exit">
        <div className="bg-accent text-accent-ink rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[85%]">
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div ref={ref} variants={messageVariants} initial="initial" animate="animate" exit="exit">
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{message.content}</p>

      {message.sources && message.sources.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => onSourceClick(isExpanded ? null : message.id)}
            className="text-xs text-ink-faint hover:text-ink-muted transition-colors flex items-center gap-1.5"
          >
            <span>{message.sources.length} fuente{message.sources.length !== 1 ? 's' : ''}</span>
            <motion.span animate={{ rotate: isExpanded ? 90 : 0 }} transition={{ duration: 0.15 }} className="text-[10px]">
              ▶
            </motion.span>
          </button>

          <motion.div
            variants={sourceVariants}
            initial="initial"
            animate={isExpanded ? 'animate' : 'initial'}
            exit="exit"
            className="overflow-hidden"
          >
            {isExpanded && (
              <div className="mt-2.5 space-y-2">
                {message.sources.map((source, idx) => (
                  <div key={idx} className="text-xs bg-surface border border-border-muted rounded-lg p-3">
                    <div className="font-medium text-ink-muted truncate">
                      {source.source_file || source.source_url || 'Fuente desconocida'}
                    </div>
                    <p className="text-ink-faint mt-1 line-clamp-2">{source.chunk_text}</p>
                    {source.source_url && (
                      <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="mt-1.5 inline-block">
                        Ver fuente →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
      )}
    </motion.div>
  )
})

export default Message
