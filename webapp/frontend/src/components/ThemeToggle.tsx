import { useTheme, type ThemePreference } from '../theme/ThemeProvider';
import { SegmentedControl } from './SegmentedControl';
import styles from './ThemeToggle.module.css';

export function ThemeToggle({ className = '' }: { className?: string }) {
  const { preference, setPreference } = useTheme();

  const options: { value: string; label: string }[] = [
    { value: 'light', label: 'Sáng' },
    { value: 'dark', label: 'Tối' },
    { value: 'system', label: 'Hệ thống' },
  ];

  return (
    <div className={`${styles.wrapper} ${className}`}>
      <SegmentedControl
        ariaLabel="Tùy chọn giao diện"
        options={options}
        value={preference}
        onChange={(val) => setPreference(val as ThemePreference)}
      />
    </div>
  );
}
