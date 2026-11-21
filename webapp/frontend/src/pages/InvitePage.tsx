import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { redeemInvite } from '../api/auth';
import { useAuth } from '../auth/AuthContext';
import { ApiError } from '../api/client';
import { TextField } from '../components/TextField';
import { Button } from '../components/Button';
import { ThemeToggle } from '../components/ThemeToggle';
import styles from './InvitePage.module.css';

export function InvitePage() {
  const [code, setCode] = useState('');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { setUser } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!code.trim()) {
      setError('Vui lòng nhập mã mời.');
      return;
    }
    if (!username.trim()) {
      setError('Vui lòng nhập tên đăng nhập.');
      return;
    }
    if (!displayName.trim()) {
      setError('Vui lòng nhập tên hiển thị.');
      return;
    }
    if (password.length < 10) {
      setError('Mật khẩu phải có ít nhất 10 ký tự.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Mật khẩu nhập lại không khớp.');
      return;
    }

    setLoading(true);

    try {
      const newUser = await redeemInvite({
        code: code.trim(),
        username: username.trim(),
        display_name: displayName.trim(),
        password,
      });
      setUser(newUser);
      navigate('/', { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Kích hoạt tài khoản không thành công. Vui lòng thử lại.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.themeToggleWrap}>
        <ThemeToggle />
      </div>

      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.brand}>Tạo tài khoản</h1>
          <p className={styles.description}>Kích hoạt tài khoản qua mã mời hệ thống</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          {error && (
            <div className={styles.errorBanner} role="alert">
              {error}
            </div>
          )}

          <TextField
            label="Mã mời"
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Nhập mã mời"
            required
            autoFocus
          />

          <TextField
            label="Tên đăng nhập"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />

          <TextField
            label="Tên hiển thị"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Ví dụ: Nguyễn Văn A"
            required
          />

          <TextField
            label="Mật khẩu"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hint="Tối thiểu 10 ký tự"
            autoComplete="new-password"
            required
          />

          <TextField
            label="Nhập lại mật khẩu"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
          />

          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={loading}
            className={styles.submitBtn}
          >
            Kích hoạt tài khoản
          </Button>
        </form>

        <div className={styles.footer}>
          <Link to="/login" className={styles.loginLink}>
            Đã có tài khoản? Đăng nhập
          </Link>
        </div>
      </div>
    </div>
  );
}
