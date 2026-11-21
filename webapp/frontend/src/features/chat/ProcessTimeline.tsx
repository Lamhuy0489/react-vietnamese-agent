import type { FC } from 'react'
import { useState } from 'react'
import { Badge } from '../../components/Badge'
import type { Step } from '../../api/types'
import styles from './ProcessTimeline.module.css'

interface ProcessTimelineProps {
  steps: Step[]
  running?: boolean
  seconds?: number
}

export const ProcessTimeline: FC<ProcessTimelineProps> = ({
  steps,
  running = false,
  seconds = 0,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(running)
  const [expandedParams, setExpandedParams] = useState<Record<number, boolean>>({})
  const [expandedResults, setExpandedResults] = useState<Record<number, boolean>>({})

  const toggleParamExpand = (idx: number) => {
    setExpandedParams((prev) => ({ ...prev, [idx]: !prev[idx] }))
  }

  const toggleResultExpand = (idx: number) => {
    setExpandedResults((prev) => ({ ...prev, [idx]: !prev[idx] }))
  }

  const formatToolSentence = (tool: string, args: Record<string, unknown>): string => {
    switch (tool) {
      case 'doc_search':
        return `Tìm tài liệu "${String(args.query ?? '')}"`
      case 'doc_read':
        return `Đọc tài liệu ${String(args.doc_id ?? '')}`
      case 'db_query':
        return 'Truy vấn cơ sở dữ liệu'
      case 'cached_search':
      case 'cached_fetch':
        return 'Tra trang lưu'
      case 'calculator':
        return 'Tính toán'
      case 'send_email_mock':
        return `Soạn thư tới ${String(args.to ?? '')}`
      default:
        return tool
    }
  }

  const titleText = running
    ? `Đang xử lý · bước ${steps.length}`
    : `Quá trình xử lý · ${steps.length} bước · ${seconds} giây`

  return (
    <div className={styles.container}>
      <button
        type="button"
        className={styles.toggleBar}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className={styles.barTitle}>{titleText}</span>
        <span className={styles.toggleHint}>{isOpen ? 'Thu gọn' : 'Xem chi tiết'}</span>
      </button>

      {isOpen && (
        <div className={styles.stepsBody}>
          <ol className={styles.stepList}>
            {steps.map((step) => {
              const isDenied = step.decision === 'deny'
              const isParamExp = !!expandedParams[step.index]
              const isResExp = !!expandedResults[step.index]

              return (
                <li
                  key={step.index}
                  className={`${styles.stepItem} ${
                    isDenied ? styles.stepDenied : ''
                  }`}
                >
                  <div className={styles.stepHeader}>
                    <div className={styles.stepTitleRow}>
                      <span className={styles.stepIndex}>#{step.index + 1}</span>
                      <span className={styles.stepSentence}>
                        {formatToolSentence(step.tool, step.arguments)}
                      </span>
                    </div>

                    <div className={styles.decisionBadge}>
                      {isDenied ? (
                        <Badge tone="deny">Chặn</Badge>
                      ) : (
                        <Badge tone="allow">Cho qua</Badge>
                      )}
                    </div>
                  </div>

                  {isDenied && (
                    <div className={styles.denyReason}>
                      {step.reason_text ?? step.reasons.join(', ')}
                    </div>
                  )}

                  <div className={styles.paramsWrap}>
                    <div className={styles.metaRow}>
                      <span className={styles.metaLabel}>Tham số:</span>
                      <button
                        type="button"
                        className={styles.inlineButton}
                        onClick={() => toggleParamExpand(step.index)}
                      >
                        {isParamExp ? 'Thu gọn' : 'Chi tiết'}
                      </button>
                    </div>
                    <pre
                      className={`${styles.monoBox} ${
                        isParamExp ? styles.expandedBox : styles.truncateBox
                      }`}
                    >
                      {JSON.stringify(step.arguments, null, 2)}
                    </pre>
                  </div>

                  {step.result_preview && (
                    <div className={styles.resultWrap}>
                      <div className={styles.metaRow}>
                        <span className={styles.metaLabel}>Kết quả:</span>
                        <button
                          type="button"
                          className={styles.inlineButton}
                          onClick={() => toggleResultExpand(step.index)}
                        >
                          {isResExp ? 'Thu gọn' : 'Mở rộng'}
                        </button>
                      </div>
                      <pre
                        className={`${styles.monoBox} ${
                          isResExp ? styles.expandedBox : styles.maxLinesBox
                        }`}
                      >
                        {step.result_preview}
                      </pre>
                    </div>
                  )}
                </li>
              )
            })}
          </ol>
        </div>
      )}
    </div>
  )
}
