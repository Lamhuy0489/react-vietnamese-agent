export type Role = 'admin' | 'presenter' | 'editor' | 'viewer';

export type Me = {
  id: number;
  username: string;
  display_name: string;
  role: Role;
  role_label: string;
  permissions: string[];
};

export type Mode = 'V3' | 'A0';

export type Source = {
  doc_id: string;
  title: string;
  content: string;
  sensitivity: 'S0' | 'S2';
  trust: 'T0' | 'T1' | 'T2';
};

export type Decision = 'allow' | 'deny';

export type Step = {
  index: number;
  tool: string;
  arguments: Record<string, unknown>;
  decision: Decision;
  reasons: string[];
  reason_text?: string;
  result_preview?: string;
};

export type OutboxStatus =
  | 'pending'
  | 'sent'
  | 'rejected'
  | 'blocked_allowlist'
  | 'over_limit'
  | 'failed';

export type OutboxItem = {
  item_id: string;
  to: string;
  subject: string;
  body: string;
  status: OutboxStatus;
  note: string;
  turn_id: string;
};

export type Citation = {
  n: number;
  doc_id: string;
  title: string;
};

export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  mode?: Mode;
  turn_id?: string;
  steps?: Step[];
  citations?: Citation[];
  running?: boolean;
  seconds?: number;
  created_at: string;
};

export type ConversationSummary = {
  id: string;
  title: string;
  mode: Mode;
  turns: number;
  updated_at: string;
};

export type TurnStats = {
  steps: number;
  blocked: number;
  model: string;
  seconds: number;
};
