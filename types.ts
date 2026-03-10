
export type Role = 'USER' | 'AGENT';
export type SessionStatus = 'OPEN' | 'RESOLVED' | 'ARCHIVED';

export interface Message {
  id: string;
  senderId: string;
  senderRole: Role;
  text: string;
  timestamp: number;
  status: 'sent' | 'delivered' | 'read';
  isInternal?: boolean; // For private agent notes
}

export interface LeadMetadata {
  browser?: string;
  location?: string;
  ip?: string;
  adId?: string;
  campaign?: string;
  agentReferralCode?: string;
  city?: string;
  device?: string;
}

export interface ChatSession {
  id: string;
  userId: string;
  userName: string;
  userAvatar: string;
  lastMessage?: string;
  updatedAt: number;
  messages: Message[];
  adSource?: string;
  unreadCount: number;
  status: SessionStatus;
  metadata?: LeadMetadata;
  assignedAgentId?: number;
  offlineNotified?: boolean;
}

export interface Agent {
  id: number;
  email: string;
  name: string;
  referralCode: string;
  isDefaultPool: boolean;
   role?: string;
  createdAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthToken {
  accessToken: string;
  tokenType: string;
  agent: Agent;
}
