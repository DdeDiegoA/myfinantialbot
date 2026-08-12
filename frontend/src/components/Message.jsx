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

const SourceItem = ({ source, idx }) => {
  const [showText, setShowText] = React.useState(false)

  return (
    <div key={idx} className="text-xs bg-surface border border-border-muted rounded-lg p-2.5">
      <button
        onClick={() => setShowText(!showText)}
        className="w-full text-left font-medium text-ink-muted hover:text-ink transition-colors flex items-center justify-between"
      >
        <span className="truncate flex-1 text-xs">{source.source_file || source.source_url || 'Fuente'}</span>
        <motion.span animate={{ rotate: showText ? 90 : 0 }} transition={{ duration: 0.15 }} className="text-[10px] flex-shrink-0 ml-2">
          ▶
        </motion.span>
      </button>

      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: showText ? 1 : 0, height: showText ? 'auto' : 0 }}
        transition={{ duration: 0.2 }}
        className="overflow-hidden"
      >
        {showText && (
          <div className="mt-1.5 pt-1.5 border-t border-border-muted">
            <p className="text-ink-faint leading-relaxed mb-1.5 text-xs">{source.chunk_text}</p>
            {source.source_url && (
              <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="inline-block text-accent hover:text-accent/80 transition-colors text-xs">
                Ver fuente →
              </a>
            )}
          </div>
        )}
      </motion.div>
    </div>
  )
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
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{message.content}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div ref={ref} variants={messageVariants} initial="initial" animate="animate" exit="exit">
      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-ink">{message.content}</p>

      {message.sources && message.sources.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => onSourceClick(isExpanded ? null : message.id)}
            className="text-xs text-ink-faint hover:text-ink-muted transition-colors flex items-center gap-1.5 mb-2"
          >
            <span className="font-medium">{message.sources.length} fuente{message.sources.length !== 1 ? 's' : ''}</span>
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
              <div className="space-y-1.5">
                {message.sources.map((source, idx) => (
                  <SourceItem key={idx} source={source} idx={idx} />
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
