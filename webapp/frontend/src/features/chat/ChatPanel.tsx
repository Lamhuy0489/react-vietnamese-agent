import type { ChangeEvent, FC, KeyboardEvent, ReactNode } from 'react'
import { useEffect, useRef, useState } from 'react'
import { Button } from '../../components/Button'
import { CitationChip } from './CitationChip'
import { ProcessTimeline } from './ProcessTimeline'
import type { Citation, Message, Mode } from '../../api/types'
import styles from './ChatPanel.module.css'

interface ChatPanelProps {
  messages: Message[]
  isStreaming: boolean
  mode: Mode
  onSend: (text: string) => void
  onCitationClick: (docId: string) => void
}

export const ChatPanel: FC<ChatPanelProps> = ({
  messages,
  isStreaming,
  mode,
  onSend,
  onCitationClick,
}) => {
  const [input, setInput] = useState<string>('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming])

  const handleTextareaChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        140
      )}px`
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    if (!input.trim() || isStreaming) return
    onSend(input)
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const renderContentWithCitations = (
    text: string,
    citations?: Citation[]
  ): ReactNode[] => {
    if (!text) return []
    const parts = text.split(/(\[\d+\])/g)
    return parts.map((part, index) => {
      const match = part.match(/^\[(\d+)\]$/)
      if (match) {
        const n = parseInt(match[1], 10)
        const cit = citations?.find((c) => c.n === n)
        return (
          <CitationChip
            key={index}
            n={n}
            title={cit ? cit.title : `Tài liệu tham chiếu [${n}]`}
            docId={cit ? cit.doc_id : ''}
            onClick={(docId) => onCitationClick(docId)}
          />
        )
      }
      return <span key={index}>{part}</span>
    })
  }

  return (
    <div className={styles.container}>
      {/* Live region for accessibility during agent processing */}
      <div className={styles.srOnly} aria-live="polite">
        {isStreaming ? 'Đang thực hiện quy trình xử lý tác vụ...' : 'Sẵn sàng'}
      </div>

      <div className={styles.messageList}>
        <div className={styles.innerList}>
          {messages.length === 0 ? (
            <div className={styles.welcomeBox}>
              <h2 className={styles.welcomeTitle}>Không gian làm việc an toàn</h2>
              <p className={styles.welcomeDesc}>
                Các hành động của agent được kiểm soát chặt chẽ bởi BrokerGuard.
                Nhập yêu cầu tra cứu quy chế, thông tin học bổng hoặc soạn thảo thư tín.
              </p>
            </div>
          ) : (
            messages.map((msg) => {
              if (msg.role === 'user') {
                return (
                  <div key={msg.id} className={styles.userRow}>
                    <div className={styles.userBubble}>{msg.content}</div>
                  </div>
                )
              }

              const modeLabel =
                (msg.mode ?? mode) === 'A0' ? 'A0 (không bảo vệ)' : 'BrokerGuard v3'

              return (
                <div key={msg.id} className={styles.assistantRow}>
                  <div className={styles.assistantHeader}>
                    Trợ lý · {modeLabel}
                  </div>

                  {(msg.steps && msg.steps.length > 0) || msg.running ? (
                    <ProcessTimeline
                      steps={msg.steps ?? []}
                      running={msg.running}
                      seconds={msg.seconds}
                    />
                  ) : null}

                  {msg.content ? (
                    <div className={styles.assistantContent}>
                      {renderContentWithCitations(msg.content, msg.citations)}
                    </div>
                  ) : msg.running ? (
                    <div className={styles.runningPlaceholder}>
                      Đang phân tích và thực thi các bước an toàn...
                    </div>
                  ) : null}
                </div>
              )
            })
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Composer Area */}
      <div className={styles.composerWrap}>
        <div className={styles.composerInner}>
          <div className={styles.inputRow}>
            <textarea
              ref={textareaRef}
              rows={1}
              className={styles.textarea}
              placeholder="Nhập yêu cầu cho agent..."
              value={input}
              disabled={isStreaming}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
            />
            <Button
              variant="primary"
              size="md"
              loading={isStreaming}
              disabled={isStreaming || !input.trim()}
              onClick={handleSend}
            >
              Gửi
            </Button>
          </div>
          <div className={styles.composerNote}>
            Mỗi tin nhắn là một tác vụ độc lập. Quá trình xử lý chỉ gồm các hành động quan sát được.
          </div>
        </div>
      </div>
    </div>
  )
}
