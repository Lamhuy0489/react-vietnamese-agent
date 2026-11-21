import type { FC } from 'react'
import { useState } from 'react'
import { useAuth } from '../../auth/AuthContext'
import { Badge } from '../../components/Badge'
import { Button } from '../../components/Button'
import type { OutboxItem, OutboxStatus } from '../../api/types'
import styles from './OutboxCard.module.css'

interface OutboxCardProps {
  item: OutboxItem
  onSend: (id: string) => void
  onReject: (id: string) => void
}

export const OutboxCard: FC<OutboxCardProps> = ({ item, onSend, onReject }) => {
  const { user } = useAuth()
  const [showBody, setShowBody] = useState<boolean>(false)
  const [showConfirm, setShowConfirm] = useState<boolean>(false)

  const canSendRealEmail = user?.permissions.includes('send_real_email') ?? false

  const renderStatusBadge = (status: OutboxStatus) => {
    switch (status) {
      case 'pending':
        return <Badge tone="pending">Chờ xác nhận</Badge>
      case 'sent':
        return <Badge tone="allow">Đã gửi</Badge>
      case 'rejected':
        return <Badge tone="neutral">Đã hủy</Badge>
      case 'blocked_allowlist':
        return <Badge tone="deny">Ngoài danh sách</Badge>
      case 'over_limit':
        return <Badge tone="deny">Hết hạn mức</Badge>
      case 'failed':
        return <Badge tone="deny">Lỗi</Badge>
      default:
        return <Badge tone="neutral">{status}</Badge>
    }
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.toRow}>
          <span className={styles.label}>Tới:</span>
          <span className={styles.to}>{item.to}</span>
        </div>
        <div>{renderStatusBadge(item.status)}</div>
      </div>

      <div className={styles.subject}>{item.subject}</div>

      {item.note && <div className={styles.note}>{item.note}</div>}

      {showBody && (
        <div className={styles.bodyPreview}>
          <pre className={styles.bodyPre}>{item.body}</pre>
        </div>
      )}

      <div className={styles.actionRow}>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowBody(!showBody)}
        >
          {showBody ? 'Thu gọn' : 'Xem'}
        </Button>

        {item.status === 'pending' && (
          <div className={styles.rightActions}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onReject(item.item_id)}
            >
              Hủy
            </Button>

            {canSendRealEmail ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowConfirm(true)}
              >
                Gửi thật
              </Button>
            ) : (
              <span className={styles.roleNotice}>
                Cần vai trò Người trình diễn để gửi
              </span>
            )}
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className={styles.modalOverlay} role="dialog" aria-modal="true">
          <div className={styles.modalCard}>
            <h4 className={styles.modalTitle}>Xác nhận gửi thư</h4>
            <p className={styles.modalText}>
              Gửi thư thật tới <span className={styles.toMono}>{item.to}</span>?
            </p>
            <div className={styles.modalButtons}>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowConfirm(false)}
              >
                Không
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setShowConfirm(false)
                  onSend(item.item_id)
                }}
              >
                Gửi
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
