import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { me as fetchMe, login as apiLogin, logout as apiLogout } from '../api/auth';
import type { Me } from '../api/types';

export interface AuthContextValue {
  user: Me | null;
  loading: boolean;
  signIn: (u: string, p: string) => Promise<Me>;
  signOut: () => Promise<void>;
  setUser: (user: Me | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;

    fetchMe()
      .then((currentUser) => {
        if (mounted) {
          setUser(currentUser);
          setLoading(false);
        }
      })
      .catch(() => {
        if (mounted) {
          setUser(null);
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  const signIn = async (u: string, p: string): Promise<Me> => {
    const loggedUser = await apiLogin(u, p);
    setUser(loggedUser);
    return loggedUser;
  };

  const signOut = async (): Promise<void> => {
    try {
      await apiLogout();
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth phải được sử dụng bên trong AuthProvider');
  }
  return context;
}
