import type { FC } from 'react'
import { useId, useMemo, useState } from 'react'
import { Badge } from '../../components/Badge'
import { Button } from '../../components/Button'
import { SegmentedControl } from '../../components/SegmentedControl'
import { TextField } from '../../components/TextField'
import type { Source } from '../../api/types'
import styles from './SourcesPanel.module.css'

type FilterType = 'all' | 'public' | 'secret' | 'external'

interface SourcesPanelProps {
  sources: Source[]
  readIds: string[]
  selectedDocId?: string | null
  onSelectDoc?: (docId: string | null) => void
  onCloseDrawer?: () => void
}

export const SourcesPanel: FC<SourcesPanelProps> = ({
  sources,
  readIds,
  selectedDocId,
  onSelectDoc,
  onCloseDrawer,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [filter, setFilter] = useState<FilterType>('all')
  const searchInputId = useId()

  const filteredSources = useMemo(() => {
    return sources.filter((item) => {
      const matchSearch = item.title
        .toLowerCase()
        .includes(searchTerm.trim().toLowerCase())

      if (!matchSearch) return false

      if (filter === 'public') return item.sensitivity === 'S0'
      if (filter === 'secret') return item.sensitivity === 'S2'
      if (filter === 'external') return item.trust === 'T1' || item.trust === 'T2'

      return true
    })
  }, [sources, searchTerm, filter])

  const previewSource = useMemo(() => {
    if (!selectedDocId) return null
    return sources.find((s) => s.doc_id === selectedDocId) ?? null
  }, [sources, selectedDocId])

  if (previewSource) {
    return (
      <div className={styles.panel}>
        <div className={styles.previewHeader}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onSelectDoc?.(null)}
          >
            Quay lại
          </Button>
          {onCloseDrawer && (
            <Button variant="ghost" size="sm" onClick={onCloseDrawer}>
              Đóng
            </Button>
          )}
        </div>

        <div className={styles.previewContent}>
          <div className={styles.previewBadges}>
            {previewSource.sensitivity === 'S0' ? (
              <Badge tone="neutral">Công khai</Badge>
            ) : (
              <Badge tone="s2">Mật</Badge>
            )}
            {previewSource.trust === 'T0' ? (
              <Badge tone="neutral">Tin cậy</Badge>
            ) : (
              <Badge tone="pending">Ngoài</Badge>
            )}
          </div>

          <h2 className={styles.previewTitle}>{previewSource.title}</h2>
          <div className={styles.docIdTag}>{previewSource.doc_id}</div>

          <div className={styles.previewBody}>
            <pre className={styles.previewPre}>{previewSource.content}</pre>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <div className={styles.headingRow}>
          <h2 className={styles.heading}>
            Nguồn <span className={styles.count}>({filteredSources.length})</span>
          </h2>
          {onCloseDrawer && (
            <Button variant="ghost" size="sm" onClick={onCloseDrawer}>
              Đóng
            </Button>
          )}
        </div>

        <div className={styles.searchWrap}>
          <TextField
            id={searchInputId}
            label="Tìm kiếm nguồn"
            placeholder="Lọc theo tiêu đề..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className={styles.filterWrap}>
          <SegmentedControl
            ariaLabel="Phân loại nguồn"
            value={filter}
            onChange={(v) => setFilter(v as FilterType)}
            options={[
              { value: 'all', label: 'Tất cả' },
              { value: 'public', label: 'Công khai' },
              { value: 'secret', label: 'Mật' },
              { value: 'external', label: 'Ngoài' },
            ]}
          />
        </div>
      </div>

      <div className={styles.list}>
        {filteredSources.length === 0 ? (
          <div className={styles.empty}>Không tìm thấy tài liệu phù hợp</div>
        ) : (
          filteredSources.map((item) => {
            const isRead = readIds.includes(item.doc_id)
            return (
              <button
                key={item.doc_id}
                type="button"
                className={styles.sourceItem}
                onClick={() => onSelectDoc?.(item.doc_id)}
              >
                <div className={styles.itemTitle}>{item.title}</div>
                <div className={styles.itemMeta}>
                  <div className={styles.itemBadges}>
                    {item.sensitivity === 'S0' ? (
                      <Badge tone="neutral">Công khai</Badge>
                    ) : (
                      <Badge tone="s2">Mật</Badge>
                    )}
                    {item.trust === 'T0' ? (
                      <Badge tone="neutral">Tin cậy</Badge>
                    ) : (
                      <Badge tone="pending">Ngoài</Badge>
                    )}
                  </div>
                  {isRead && (
                    <span className={styles.readNotice}>
                      Đã đọc trong lượt này
                    </span>
                  )}
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
