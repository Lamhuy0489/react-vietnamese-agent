import { api } from './client';
import type { Me } from './types';

export interface RedeemInvitePayload {
  code: string;
  username: string;
  display_name: string;
  password: string;
}

export function login(username: string, password: string): Promise<Me> {
  return api<Me>('/api/auth/login', {
    method: 'POST',
    body: { username, password },
  });
}

export function logout(): Promise<void> {
  return api<void>('/api/auth/logout', {
    method: 'POST',
  });
}

export function me(): Promise<Me> {
  return api<Me>('/api/me');
}

export function redeemInvite(payload: RedeemInvitePayload): Promise<Me> {
  return api<Me>('/api/auth/redeem-invite', {
    method: 'POST',
    body: payload,
  });
}
