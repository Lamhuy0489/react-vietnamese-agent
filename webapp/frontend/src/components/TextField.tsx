import { useId, forwardRef, type InputHTMLAttributes } from 'react';
import styles from './TextField.module.css';

export interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, error, hint, id: providedId, className = '', ...rest },
  ref,
) {
  const autoId = useId();
  const inputId = providedId || autoId;
  const hintId = `${inputId}-hint`;
  const errorId = `${inputId}-error`;

  const ariaDescribedBy = [
    error ? errorId : '',
    hint ? hintId : '',
    rest['aria-describedby'] || '',
  ]
    .filter(Boolean)
    .join(' ') || undefined;

  return (
    <div className={styles.wrapper}>
      <label htmlFor={inputId} className={styles.label}>
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={ariaDescribedBy}
        className={`${styles.input} ${error ? styles.inputError : ''} ${className}`}
        {...rest}
      />
      {error && (
        <p id={errorId} className={styles.error} role="alert">
          {error}
        </p>
      )}
      {!error && hint && (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      )}
    </div>
  );
});
