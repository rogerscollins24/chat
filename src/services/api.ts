/// <reference types="vite/client" />
// API Service for LeadPulse Chat System
// Handles all communication with the Python backend

const rawApiUrl = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const API_BASE_URL = rawApiUrl
  ? (rawApiUrl.endsWith("/api") ? rawApiUrl : `${rawApiUrl}/api`)
  : "/api";

export interface Session {
  id: number;
  user_id: string;
  user_name: string;
  user_avatar?: string;
  ad_source: string;
  status: "OPEN" | "RESOLVED";
  created_at: string;
  updated_at: string;
   assigned_agent_id?: number;
  messages: Message[];
  lead_metadata?: LeadMetadata;
}

export interface Message {
  id: number;
  session_id: number;
  sender_id: string;
  sender_role: "USER" | "AGENT";
  text: string;
  is_internal: boolean;
  timestamp: string;
}

export interface LeadMetadata {
  id: number;
  session_id: number;
  ip?: string;
  location?: string;
  browser?: string;
  city?: string;
  device?: string;
  ad_id?: string;
  agent_referral_code?: string;
}

export interface Agent {
  id: number;
  email: string;
  name: string;
  referral_code: string;
  is_default_pool: boolean;
  role?: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  agent: Agent;
}

// Token management
let authToken: string | null = null;

export function setAuthToken(token: string) {
  authToken = token;
  localStorage.setItem('agent_token', token);
}

export function getAuthToken(): string | null {
  if (!authToken) {
    authToken = localStorage.getItem('agent_token');
  }
  return authToken;
}

export function clearAuthToken() {
  authToken = null;
  localStorage.removeItem('agent_token');
}

/**
 * Check if session has been invalidated (401 response means old session)
 */
export function isSessionExpired(error: any): boolean {
  return error?.status === 401 && error?.detail?.includes("Session expired");
}

/**
 * Handle 401 errors by clearing token and notifying caller
 */
export function handleAuthError(error: any): void {
  if (error?.status === 401) {
    clearAuthToken();
  }
}

function getApiErrorMessage(error: any, fallback: string): string {
  const detail = error?.detail;
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first?.msg === 'string' && first.msg.trim()) {
      return first.msg;
    }
  }
  return fallback;
}

// ==================== AGENT ENDPOINTS ====================

/**
 * Register a new agent
 */
export async function registerAgent(
  email: string,
  password: string,
  name: string,
  isDefaultPool: boolean = false
): Promise<Agent> {
  const response = await fetch(`${API_BASE_URL}/agents/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
      name,
      is_default_pool: isDefaultPool,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to register agent");
  }

  return response.json();
}

/**
 * Login an agent
 */
export async function loginAgent(email: string, password: string): Promise<TokenResponse> {
  const maxAttempts = 2;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 60000);

    try {
      const response = await fetch(`${API_BASE_URL}/agents/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        let error: any = null;
        try {
          error = await response.json();
        } catch {
          // Upstream can return empty/non-JSON responses while unhealthy.
        }

        if (response.status >= 500) {
          throw new Error("Backend is waking up or temporarily unavailable. Please retry in a few seconds.");
        }

        throw new Error(getApiErrorMessage(error, "Failed to login"));
      }

      const data: TokenResponse = await response.json();
      setAuthToken(data.access_token);
      return data;
    } catch (error: any) {
      const isRetryable = error?.name === "AbortError" || error instanceof TypeError;
      if (isRetryable && attempt < maxAttempts) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        continue;
      }

      if (error?.name === "AbortError") {
        throw new Error("Login request timed out. Backend may be cold-starting; please try again in 30-60 seconds.");
      }
      if (error instanceof TypeError) {
        throw new Error("Unable to reach the server. Backend may still be deploying.");
      }
      throw error;
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  throw new Error("Failed to login");
}

/**
 * Get current agent profile
 */
export async function getCurrentAgent(): Promise<Agent> {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(`${API_BASE_URL}/agents/me`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken();
    }
    throw new Error("Failed to get agent profile");
  }

  return response.json();
}

// ==================== SESSION ENDPOINTS ====================

/**
 * Create a new chat session
 */
export async function createSession(
  user_id: string,
  user_name: string,
  ad_source: string,
  user_avatar?: string,
  referral_code?: string,
  metadata?: Partial<LeadMetadata>
): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id,
      user_name,
      user_avatar,
      ad_source,
      referral_code,
      lead_metadata: metadata,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get all sessions (for Agent dashboard)
 */
export async function listSessions(
  status?: "OPEN" | "RESOLVED",
  skip: number = 0,
  limit: number = 100,
  includeAll: boolean = false
): Promise<Session[]> {
  const params = new URLSearchParams();
  if (status) params.append("status", status);
  params.append("skip", skip.toString());
  params.append("limit", limit.toString());
  if (includeAll) params.append("include_all", "true");

  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/sessions?${params.toString()}`,
    {
      method: "GET",
      headers,
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch sessions: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get a specific session by ID
 */
export async function getSession(sessionId: number): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch session: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update session status or details
 */
export async function updateSession(
  sessionId: number,
  updates: {
    status?: "OPEN" | "RESOLVED";
    user_name?: string;
    user_avatar?: string;
  }
): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Failed to update session: ${response.statusText}`);
  }

  return response.json();
}

// ==================== MESSAGE ENDPOINTS ====================

/**
 * Get all messages for a session
 */
export async function getSessionMessages(
  sessionId: number,
  skip: number = 0,
  limit: number = 100
): Promise<Message[]> {
  const params = new URLSearchParams();
  params.append("skip", skip.toString());
  params.append("limit", limit.toString());

  const response = await fetch(
    `${API_BASE_URL}/sessions/${sessionId}/messages?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch messages: ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Send a message to a session
 */
export async function sendMessage(
  sessionId: number,
  senderId: string,
  senderRole: "USER" | "AGENT",
  text: string,
  isInternal: boolean = false
): Promise<Message> {
  const response = await fetch(`${API_BASE_URL}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(getAuthToken() ? { "Authorization": `Bearer ${getAuthToken()}` } : {}),
    },
    body: JSON.stringify({
      session_id: sessionId,
      sender_id: senderId,
      sender_role: senderRole,
      text,
      is_internal: isInternal,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }

  return response.json();
}

// ==================== SUPER ADMIN ENDPOINTS ====================

function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token
    ? { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }
    : { "Content-Type": "application/json" };
}

export async function adminListAgents(): Promise<Agent[]> {
  const response = await fetch(`${API_BASE_URL}/agents`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Failed to list agents");
  return response.json();
}

export async function adminCreateAgent(agent: { email: string; password: string; name: string; is_default_pool?: boolean; role?: string; }): Promise<Agent> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 30000);

  try {
    const response = await fetch(`${API_BASE_URL}/admin/agents`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(agent),
      signal: controller.signal,
    });
    
    window.clearTimeout(timeoutId);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
      console.error('❌ Agent creation failed:', error);
      throw new Error(getApiErrorMessage(error, "Failed to create agent"));
    }
    return response.json();
  } catch (error: any) {
    window.clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out creating agent. Please check backend health.');
    }
    throw error;
  }
}

export async function adminUpdateAgent(agentId: number, updates: { email?: string; name?: string; password?: string; is_default_pool?: boolean; role?: string; }): Promise<Agent> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/${agentId}`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error("Failed to update agent");
  return response.json();
}

export async function adminRotateReferral(agentId: number): Promise<Agent> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/${agentId}/referral`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({})
  });
  if (!response.ok) throw new Error("Failed to rotate referral code");
  return response.json();
}

export async function adminResetPassword(agentId: number, newPassword: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/${agentId}/reset_password`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ new_password: newPassword })
  });
  if (!response.ok) throw new Error("Failed to reset password");
}

export async function adminDeleteAgent(agentId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/${agentId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error("Failed to delete agent");
}

export interface MessageTemplate {
  id: number;
  text: string;
  created_at: string;
  updated_at: string;
}

export async function listMessageTemplates(): Promise<MessageTemplate[]> {
  const response = await fetch(`${API_BASE_URL}/templates`, {
    method: "GET",
    headers: authHeaders(),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to list templates");
  }
  return response.json();
}

export async function createMessageTemplate(text: string): Promise<MessageTemplate> {
  const response = await fetch(`${API_BASE_URL}/templates`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to save template");
  }
  return response.json();
}

export async function deleteMessageTemplate(templateId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to delete template");
  }
}

export async function adminListSessions(params: { status?: "OPEN" | "RESOLVED"; agent_id?: number; skip?: number; limit?: number } = {}): Promise<Session[]> {
  const search = new URLSearchParams();
  if (params.status) search.append("status", params.status);
  if (params.agent_id !== undefined) search.append("agent_id", params.agent_id.toString());
  search.append("skip", String(params.skip ?? 0));
  search.append("limit", String(params.limit ?? 200));
  const response = await fetch(`${API_BASE_URL}/admin/sessions?${search.toString()}`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Failed to list sessions");
  return response.json();
}

export async function adminReassignSession(sessionId: number, agentId: number): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/admin/sessions/${sessionId}/assign`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify({ agent_id: agentId })
  });
  if (!response.ok) throw new Error("Failed to reassign session");
  return response.json();
}

export async function adminExportSessions(params: { status?: "OPEN" | "RESOLVED"; agent_id?: number } = {}): Promise<any> {
  const search = new URLSearchParams();
  if (params.status) search.append("status", params.status);
  if (params.agent_id !== undefined) search.append("agent_id", params.agent_id.toString());
  const response = await fetch(`${API_BASE_URL}/admin/export/sessions?${search.toString()}`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Failed to export sessions");
  return response.json();
}

export interface OverflowAgent {
  id: number;
  name: string;
  email: string;
  role?: string;
  session_count_24h: number;
  is_overflowed: boolean;
}

export async function getOverflowAgents(): Promise<{ agents: OverflowAgent[]; overflow_threshold: number }> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/overflow`, { headers: authHeaders() });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to fetch overflow agents");
  }
  return response.json();
}

export async function reassignSessions(fromAgentId: number, toAgentId: number): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/admin/reassign-sessions`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      from_agent_id: fromAgentId,
      to_agent_id: toAgentId
    })
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to reassign sessions");
  }
  return response.json();
}

// ==================== WebSocket SUPPORT ====================

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: number;
  private listeners: {
    onMessage?: (message: Message) => void;
    onSessionUpdate?: (session: Partial<Session>) => void;
    onError?: (error: Error) => void;
    onClose?: (data: any) => void;
  } = {};

  constructor(sessionId: number) {
    this.sessionId = sessionId;
  }

  /**
   * Connect to WebSocket
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl =
        import.meta.env.VITE_WS_URL ||
        `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${this.sessionId}`;

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log(`WebSocket connected for session ${this.sessionId}`);
          resolve();
        };

        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === "message" && this.listeners.onMessage) {
            this.listeners.onMessage(data.data);
          } else if (
            data.type === "session_update" &&
            this.listeners.onSessionUpdate
          ) {
            this.listeners.onSessionUpdate(data.data);
          }
        };

        this.ws.onerror = (error) => {
          const err = new Error("WebSocket error");
          console.error(err);
          if (this.listeners.onError) {
            this.listeners.onError(err);
          }
          reject(err);
        };

        this.ws.onclose = (event) => {
          console.log(`WebSocket disconnected for session ${this.sessionId}`);
          if (this.listeners.onClose) {
            this.listeners.onClose(event);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Send a message through WebSocket
   */
  public sendMessage(
    senderId: string,
    text: string,
    senderRole: "USER" | "AGENT" = "USER"
  ): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not connected");
    }

    this.ws.send(
      JSON.stringify({
        type: "message",
        sender_id: senderId,
        sender_role: senderRole,
        text,
      })
    );
  }

  /**
   * Register event listeners
   */
  public on(
    event: "message" | "sessionUpdate" | "error" | "close",
    callback: (data: any) => void
  ): void {
    switch (event) {
      case "message":
        this.listeners.onMessage = callback;
        break;
      case "sessionUpdate":
        this.listeners.onSessionUpdate = callback;
        break;
      case "error":
        this.listeners.onError = callback;
        break;
      case "close":
        this.listeners.onClose = callback;
        break;
    }
  }

  /**
   * Disconnect WebSocket
   */
  public disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Check if WebSocket is connected
   */
  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// ==================== POLLING FALLBACK (Optional) ====================

/**
 * Poll for messages when WebSocket is not available
 */
export async function pollSessionMessages(
  sessionId: number,
  interval: number = 2000,
  onNewMessage?: (message: Message) => void,
  onStop?: () => void
): Promise<() => void> {
  let lastMessageId = 0;
  let isPolling = true;

  const poll = async () => {
    if (!isPolling) return;

    try {
      const messages = await getSessionMessages(sessionId);
      
      messages.forEach((message) => {
        if (message.id > lastMessageId) {
          lastMessageId = message.id;
          if (onNewMessage) {
            onNewMessage(message);
          }
        }
      });
    } catch (error) {
      console.error("Polling error:", error);
    }

    setTimeout(poll, interval);
  };

  // Start polling
  poll();

  // Return stop function
  return () => {
    isPolling = false;
    if (onStop) onStop();
  };
}

// ==================== UTILITY ====================

/**
 * Check API health
 */
export async function checkAPIHealth(): Promise<boolean> {
  try {
    const baseUrl = API_BASE_URL.replace("/api", "");
    const response = await fetch(`${baseUrl}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
