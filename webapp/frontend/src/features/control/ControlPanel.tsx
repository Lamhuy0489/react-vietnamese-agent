import type { FC } from 'react'
import { Badge } from '../../components/Badge'
import { Button } from '../../components/Button'
import { OutboxCard } from './OutboxCard'
import type { Decision, OutboxItem, TurnStats } from '../../api/types'
import styles from './ControlPanel.module.css'

type DecisionItem = {
  id: string
  time: string
  tool: string
  decision: Decision
  reason?: string
}

interface ControlPanelProps {
  outboxItems: OutboxItem[]
  turnStats?: TurnStats
  decisions: DecisionItem[]
  onSendRealEmail: (id: string) => void
  onRejectEmail: (id: string) => void
  onCloseDrawer?: () => void
}

export const ControlPanel: FC<ControlPanelProps> = ({
  outboxItems,
  turnStats,
  decisions,
  onSendRealEmail,
  onRejectEmail,
  onCloseDrawer,
}) => {
  const pendingCount = outboxItems.filter((i) => i.status === 'pending').length

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2 className={styles.title}>Kiểm soát & Hộp thư</h2>
        {onCloseDrawer && (
          <Button variant="ghost" size="sm" onClick={onCloseDrawer}>
            Đóng
          </Button>
        )}
      </div>

      <div className={styles.body}>
        {/* Section 1: Outbox */}
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h3 className={styles.sectionTitle}>
              Hộp thư chờ <span className={styles.badgeCount}>({pendingCount})</span>
            </h3>
          </div>

          <div className={styles.outboxList}>
            {outboxItems.length === 0 ? (
              <div className={styles.emptyNotice}>
                Không có thư nào trong hàng đợi
              </div>
            ) : (
              outboxItems.map((item) => (
                <OutboxCard
                  key={item.item_id}
                  item={item}
                  onSend={onSendRealEmail}
                  onReject={onRejectEmail}
                />
              ))
            )}
          </div>
        </section>

        {/* Section 2: Turn Stats */}
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h3 className={styles.sectionTitle}>Lượt này</h3>
          </div>

          <dl className={styles.statsDl}>
            <div className={styles.statRow}>
              <dt className={styles.statLabel}>Số bước</dt>
              <dd className={styles.statValue}>{turnStats?.steps ?? 0}</dd>
            </div>
            <div className={styles.statRow}>
              <dt className={styles.statLabel}>Bị chặn</dt>
              <dd className={styles.statValue}>{turnStats?.blocked ?? 0}</dd>
            </div>
            <div className={styles.statRow}>
              <dt className={styles.statLabel}>Mô hình</dt>
              <dd className={styles.statValue}>{turnStats?.model ?? 'BrokerGuard Core v3'}</dd>
            </div>
            <div className={styles.statRow}>
              <dt className={styles.statLabel}>Thời gian</dt>
              <dd className={styles.statValue}>{turnStats?.seconds ?? 0} giây</dd>
            </div>
          </dl>
        </section>

        {/* Section 3: Control Log */}
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h3 className={styles.sectionTitle}>Nhật ký kiểm soát</h3>
          </div>

          <div className={styles.logList}>
            {decisions.length === 0 ? (
              <div className={styles.emptyNotice}>Chưa có quyết định nào</div>
            ) : (
              decisions.map((dec) => (
                <div key={dec.id} className={styles.logItem}>
                  <div className={styles.logTop}>
                    <span className={styles.logTime}>{dec.time}</span>
                    <span className={styles.logTool}>{dec.tool}</span>
                    <span className={styles.logBadge}>
                      {dec.decision === 'allow' ? (
                        <Badge tone="allow">Cho qua</Badge>
                      ) : (
                        <Badge tone="deny">Chặn</Badge>
                      )}
                    </span>
                  </div>
                  {dec.reason && (
                    <div className={styles.logReason}>{dec.reason}</div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
