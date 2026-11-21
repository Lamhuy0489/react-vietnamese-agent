import { type ReactNode, type MouseEventHandler } from 'react';
import styles from './Card.module.css';

export interface CardProps {
  as?: 'div' | 'section' | 'article';
  padded?: boolean;
  className?: string;
  children: ReactNode;
  onClick?: MouseEventHandler<HTMLElement>;
}

export function Card({
  as: Component = 'div',
  padded = true,
  className = '',
  children,
  onClick,
}: CardProps) {
  const isClickable = Boolean(onClick);
  const classes = [
    styles.card,
    padded ? styles.padded : '',
    isClickable ? styles.clickable : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <Component
      className={classes}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={
        isClickable
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick?.(e as unknown as React.MouseEvent<HTMLElement>);
              }
            }
          : undefined
      }
    >
      {children}
    </Component>
  );
}
