import type { FC } from 'react'
import styles from './CitationChip.module.css'

interface CitationChipProps {
  n: number
  title: string
  docId: string
  onClick: (docId: string) => void
}

export const CitationChip: FC<CitationChipProps> = ({
  n,
  title,
  docId,
  onClick,
}) => {
  return (
    <button
      type="button"
      className={styles.chip}
      title={title}
      onClick={() => onClick(docId)}
    >
      [{n}]
    </button>
  )
}
