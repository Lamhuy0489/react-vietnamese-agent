import type { FC } from 'react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { mockConversations } from '../mocks/data'
import type { ConversationSummary } from '../api/types'
import styles from './HomePage.module.css'

export const HomePage: FC = () => {
  const navigate = useNavigate()
  const [conversations] = useState<ConversationSummary[]>(mockConversations)

  const handleCreateNew = () => {
    const newId = `conv-${Date.now()}`
    navigate(`/c/${newId}`)
  }

  const formatDate = (isoString: string): string => {
    try {
      const d = new Date(isoString)
      return new Intl.DateTimeFormat('vi-VN', {
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(d)
    } catch {
      return isoString
    }
  }

  return (
    <div className={styles.page}>
      <AppHeader />
      <main className={styles.main}>
        <div className={styles.contentWrap}>
          <div className={styles.headerRow}>
            <div>
              <h1 className={styles.title}>Hội thoại</h1>
              <p className={styles.subtitle}>
                Các phiên làm việc với trợ lý đã được ghi nhận trong hệ thống
              </p>
            </div>
            <Button variant="primary" size="md" onClick={handleCreateNew}>
              Hội thoại mới
            </Button>
          </div>

          {conversations.length === 0 ? (
            <EmptyState
              title="Chưa có hội thoại nào"
              description="Bắt đầu phiên làm việc mới để tương tác với trợ lý được bảo vệ bởi BrokerGuard."
              action={
                <Button variant="primary" onClick={handleCreateNew}>
                  Tạo hội thoại mới
                </Button>
              }
            />
          ) : (
            <div className={styles.grid}>
              {conversations.map((conv) => {
                const modeLabel =
                  conv.mode === 'V3' ? 'BrokerGuard v3' : 'Không kiểm soát (A0)'
                return (
                  <Card
                    key={conv.id}
                    as="article"
                    padded
                    className={styles.convCard}
                    onClick={() => navigate(`/c/${conv.id}`)}
                  >
                    <div className={styles.cardHeader}>
                      <h2 className={styles.cardTitle}>{conv.title}</h2>
                    </div>
                    <div className={styles.cardMeta}>
                      <span className={styles.turnInfo}>
                        {conv.turns} lượt · {modeLabel}
                      </span>
                      <time className={styles.timestamp} dateTime={conv.updated_at}>
                        {formatDate(conv.updated_at)}
                      </time>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
