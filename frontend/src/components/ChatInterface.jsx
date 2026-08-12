import React, { useState } from 'react'
import MessageList from './MessageList'
import InputBox from './InputBox'

function ChatInterface({ messages, loading, onSendMessage, messagesEndRef }) {
  const [expandedSource, setExpandedSource] = useState(null)

  return (
    <div className="flex flex-col h-full">
      <header className="border-b border-border-muted">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-2.5 min-w-0">
          <span className="w-6 h-6 rounded-md bg-accent flex items-center justify-center text-accent-ink text-xs font-semibold flex-shrink-0">
            M
          </span>
          <h1 className="text-sm font-medium text-ink truncate">MyFinancialBot</h1>
          <span className="hidden sm:inline text-xs text-ink-faint truncate">DIAN · Impuestos Colombia</span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto overflow-x-hidden">
        <div className="max-w-2xl mx-auto">
          <MessageList
            messages={messages}
            loading={loading}
            expandedSource={expandedSource}
            onSourceClick={setExpandedSource}
          />
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-border-muted">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4">
          <InputBox onSendMessage={onSendMessage} disabled={loading} />
          <p className="text-xs text-ink-faint text-center mt-2.5">
            MyFinancialBot puede cometer errores. Verifica la información oficial en la DIAN.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
