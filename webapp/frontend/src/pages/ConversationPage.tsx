import type { FC } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { AppHeader } from '../components/AppHeader'
import { Button } from '../components/Button'
import { SegmentedControl } from '../components/SegmentedControl'
import { ChatPanel } from '../features/chat/ChatPanel'
import { ControlPanel } from '../features/control/ControlPanel'
import { SourcesPanel } from '../features/sources/SourcesPanel'
import {
  mockConversations,
  mockDefaultTurnStats,
  mockInitialMessages,
  mockInitialOutboxItems,
  mockSources,
} from '../mocks/data'
import { simulateAgentTurn } from '../mocks/simulate'
import type {
  Decision,
  Message,
  Mode,
  OutboxItem,
  Source,
  Step,
  TurnStats,
} from '../api/types'
import styles from './ConversationPage.module.css'

type DecisionLogItem = {
  id: string
  time: string
  tool: string
  decision: Decision
  reason?: string
}

export const ConversationPage: FC = () => {
  const { id = 'conv-01' } = useParams<{ id: string }>()
  const { user } = useAuth()

  const conversationMeta = useMemo(() => {
    return (
      mockConversations.find((c) => c.id === id) ?? {
        id,
        title: id === 'new' ? 'Hội thoại mới' : 'Phiên làm việc mới',
        mode: 'V3' as Mode,
        turns: 0,
        updated_at: new Date().toISOString(),
      }
    )
  }, [id])

  const [mode, setMode] = useState<Mode>(conversationMeta.mode)
  const [messages, setMessages] = useState<Message[]>(() => {
    return mockInitialMessages[id] ?? []
  })
  const [sources] = useState<Source[]>(mockSources)
  const [readDocIds, setReadDocIds] = useState<string[]>(() => {
    const ids = new Set<string>()
    const initMsgs = mockInitialMessages[id] ?? []
    initMsgs.forEach((m) => {
      m.steps?.forEach((st) => {
        if (st.tool === 'doc_read' && typeof st.arguments.doc_id === 'string') {
          ids.add(st.arguments.doc_id)
        }
      })
      m.citations?.forEach((c) => ids.add(c.doc_id))
    })
    return Array.from(ids)
  })

  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [outboxItems, setOutboxItems] = useState<OutboxItem[]>(mockInitialOutboxItems)
  const [turnStats, setTurnStats] = useState<TurnStats>(mockDefaultTurnStats)
  const [decisions, setDecisions] = useState<DecisionLogItem[]>([
    {
      id: 'dec-01',
      time: '08:29:11',
      tool: 'doc_search',
      decision: 'allow',
      reason: 'Truy vấn tài liệu công khai',
    },
    {
      id: 'dec-02',
      time: '08:29:12',
      tool: 'doc_read',
      decision: 'allow',
      reason: 'Đọc tài liệu S0',
    },
  ])

  const [isStreaming, setIsStreaming] = useState<boolean>(false)
  const [leftDrawerOpen, setLeftDrawerOpen] = useState<boolean>(false)
  const [rightDrawerOpen, setRightDrawerOpen] = useState<boolean>(false)

  const abortSimulationRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    return () => {
      if (abortSimulationRef.current) {
        abortSimulationRef.current()
      }
    }
  }, [])

  const canSwitchMode = user?.permissions.includes('switch_mode') ?? false

  const handleModeChange = (val: string) => {
    if (val === 'V3' || val === 'A0') {
      setMode(val)
    }
  }

  const handleSelectDoc = useCallback((docId: string | null) => {
    setSelectedDocId(docId)
    if (docId) {
      setLeftDrawerOpen(true)
    }
  }, [])

  const handleSend = (text: string) => {
    if (isStreaming || !text.trim()) return

    const nowIso = new Date().toISOString()
    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text.trim(),
      created_at: nowIso,
    }

    const assistantMsgId = `a-${Date.now()}`
    const pendingAssistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      mode,
      content: '',
      running: true,
      steps: [],
      citations: [],
      seconds: 0,
      created_at: nowIso,
    }

    setMessages((prev) => [...prev, userMsg, pendingAssistantMsg])
    setIsStreaming(true)

    const startTime = Date.now()
    let blockedCount = 0
    let stepCount = 0

    abortSimulationRef.current = simulateAgentTurn(text, mode, {
      onStep: (step: Step) => {
        stepCount += 1
        if (step.decision === 'deny') {
          blockedCount += 1
        }

        if (step.tool === 'doc_read' && typeof step.arguments.doc_id === 'string') {
          const did = step.arguments.doc_id
          setReadDocIds((prev) => (prev.includes(did) ? prev : [...prev, did]))
        }

        const now = new Date()
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(
          now.getMinutes()
        ).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`

        setDecisions((prev) => [
          {
            id: `dec-${Date.now()}-${step.index}`,
            time: timeStr,
            tool: step.tool,
            decision: step.decision,
            reason: step.reason_text ?? step.reasons.join(', '),
          },
          ...prev,
        ])

        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === assistantMsgId) {
              const currentSteps = m.steps ?? []
              return {
                ...m,
                steps: [...currentSteps, step],
              }
            }
            return m
          })
        )
      },
      onFinish: (finalContent, citations, outbox) => {
        const elapsedSeconds = Math.max(
          1,
          Math.round((Date.now() - startTime) / 1000)
        )

        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === assistantMsgId) {
              return {
                ...m,
                content: finalContent,
                citations,
                running: false,
                seconds: elapsedSeconds,
              }
            }
            return m
          })
        )

        if (outbox) {
          setOutboxItems((prev) => [outbox, ...prev])
        }

        setTurnStats({
          steps: stepCount,
          blocked: blockedCount,
          model:
            mode === 'V3'
              ? 'BrokerGuard Core v3 (Qwen-2.5-72B)'
              : 'Qwen-2.5-72B (Không qua bộ lọc)',
          seconds: elapsedSeconds,
        })

        setIsStreaming(false)
        abortSimulationRef.current = null
      },
      onError: () => {
        setIsStreaming(false)
        abortSimulationRef.current = null
      },
    })
  }

  const handleSendRealEmail = (itemId: string) => {
    setOutboxItems((prev) =>
      prev.map((it) => (it.item_id === itemId ? { ...it, status: 'sent' } : it))
    )
  }

  const handleRejectEmail = (itemId: string) => {
    setOutboxItems((prev) =>
      prev.map((it) =>
        it.item_id === itemId ? { ...it, status: 'rejected' } : it
      )
    )
  }

  const headerLeftSlot = (
    <div className={styles.headerLeft}>
      <Link to="/" className={styles.backLink}>
        Hội thoại
      </Link>
      <span className={styles.divider}>/</span>
      <span className={styles.convTitle}>{conversationMeta.title}</span>
    </div>
  )

  const headerRightSlot = (
    <div className={styles.headerRight}>
      <div className={styles.responsiveDrawerToggles}>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setLeftDrawerOpen((prev) => !prev)
            setRightDrawerOpen(false)
          }}
        >
          Nguồn
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setRightDrawerOpen((prev) => !prev)
            setLeftDrawerOpen(false)
          }}
        >
          Kiểm soát
        </Button>
      </div>

      <div className={styles.modeControlWrap}>
        <SegmentedControl
          ariaLabel="Chọn chế độ vận hành"
          value={mode}
          onChange={handleModeChange}
          options={[
            { value: 'V3', label: 'BrokerGuard v3' },
            {
              value: 'A0',
              label: 'A0',
              disabled: !canSwitchMode,
            },
          ]}
        />
      </div>
    </div>
  )

  return (
    <div className={styles.container}>
      <AppHeader left={headerLeftSlot} right={headerRightSlot} />

      <div className={styles.workspace}>
        {/* Left Column / Drawer: Sources */}
        <aside
          className={`${styles.leftColumn} ${
            leftDrawerOpen ? styles.drawerOpen : ''
          }`}
        >
          <SourcesPanel
            sources={sources}
            readIds={readDocIds}
            selectedDocId={selectedDocId}
            onSelectDoc={handleSelectDoc}
            onCloseDrawer={() => setLeftDrawerOpen(false)}
          />
        </aside>

        {/* Backdrop for mobile drawers */}
        {(leftDrawerOpen || rightDrawerOpen) && (
          <div
            className={styles.backdrop}
            onClick={() => {
              setLeftDrawerOpen(false)
              setRightDrawerOpen(false)
            }}
          />
        )}

        {/* Center Column: Chat */}
        <main className={styles.centerColumn}>
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            mode={mode}
            onSend={handleSend}
            onCitationClick={handleSelectDoc}
          />
        </main>

        {/* Right Column / Drawer: Control & Outbox */}
        <aside
          className={`${styles.rightColumn} ${
            rightDrawerOpen ? styles.drawerOpen : ''
          }`}
        >
          <ControlPanel
            outboxItems={outboxItems}
            turnStats={turnStats}
            decisions={decisions}
            onSendRealEmail={handleSendRealEmail}
            onRejectEmail={handleRejectEmail}
            onCloseDrawer={() => setRightDrawerOpen(false)}
          />
        </aside>
      </div>
    </div>
  )
}
