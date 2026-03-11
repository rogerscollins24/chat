
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { ChatSession, Message, Role, SessionStatus } from './types';
import { INITIAL_SESSIONS, AD_SOURCES } from './constants';
import { SendIcon } from './components/Icons';
import * as api from './src/services/api';
import SuperAdminDashboard from './components/SuperAdminDashboard';

/**
 * ARCHITECTURAL NOTE: 
 * This app is designed to be served from two different URLs.
 * 1. The root '/' is for the Lead/Client end.
 * 2. The '/admin' path is for the Agent/Internal end.
 * In a real deployment, these could be separate apps sharing this codebase.
 */

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!isAuthenticated || !currentAgent) {
      if (ws) {
        ws.close();
        setWs(null);
      }
      return;
    }

    const token = api.getAuthToken();
    const rawApiUrl = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
    const normalizedApiUrl = rawApiUrl && !rawApiUrl.endsWith('/api') ? `${rawApiUrl}/api` : rawApiUrl;
    const wsBase = normalizedApiUrl
      ? normalizedApiUrl.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api`;

    const wsUrl = token
      ? `${wsBase}/ws?token=${encodeURIComponent(token)}`
      : `${wsBase}/ws`;

    let retryCount = 0;
    let reconnectTimer: number | undefined;
    let closed = false;
    let hasOpened = false;
    let activeSocket: WebSocket | null = null;

    const scheduleReconnect = () => {
      if (closed) return;
      const baseDelay = Math.min(30000, 1000 * Math.pow(2, retryCount));
      const jitter = Math.floor(Math.random() * 300);
      const delay = baseDelay + jitter;
      retryCount += 1;
      reconnectTimer = window.setTimeout(connect, delay);
    };

    const connect = () => {
      if (closed) return;
      const websocket = new WebSocket(wsUrl);
      activeSocket = websocket;

      websocket.onopen = () => {
        hasOpened = true;
        retryCount = 0;
        websocket.send(JSON.stringify({
          type: 'subscribe',
          agent_id: currentAgent.id
        }));
        setWs(websocket);
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'message') {
            const messageData = data.data;
            const backendSessionId = messageData.session_id;
            const sessionId = `backend-${backendSessionId}`;

            // Store in localStorage to trigger other tabs
            localStorage.setItem('ws_message', JSON.stringify({
              sessionId,
              messageData,
              timestamp: Date.now()
            }));

            // Add or update message in the session
            setSessions(prev => prev.map(session => {
              if (session.id === sessionId) {
                const newMessage: Message = {
                  id: `m-${messageData.id}`,
                  senderId: messageData.sender_id,
                  senderRole: messageData.sender_role as Role,
                  text: messageData.text,
                  timestamp: new Date(messageData.timestamp).getTime(),
                  status: 'sent',
                  isInternal: messageData.is_internal || false
                };
                return {
                  ...session,
                  messages: [...session.messages, newMessage],
                  lastMessage: newMessage.text,
                  updatedAt: Date.now(),
                  unreadCount: session.id === currentSessionId ? 0 : session.unreadCount + 1
                };
              }
              return session;
            }));
          } else if (data.type === 'session_created') {
            loadBackendSessions();
          }
        } catch (error) {
          // Error processing WebSocket message
        }
      };

      websocket.onclose = () => {
        setWs(prev => (prev === websocket ? null : prev));
        if (!closed) {
          scheduleReconnect();
        }
      };

      websocket.onerror = () => {
        setWs(prev => (prev === websocket ? null : prev));
        if (!closed && !hasOpened) {
          scheduleReconnect();
        }
      };
    };

    // Small delay helps avoid cold-start WebSocket failures.
    reconnectTimer = window.setTimeout(connect, 1500);

    return () => {
      closed = true;
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      if (activeSocket) {
        activeSocket.close();
      }
    };
  }, [isAuthenticated, currentAgent]);

  const handleTemplateSave = async () => {
    if (!templateInput.trim()) return;
    if (templateLimitReached) {
      setTemplateActionError('Maximum of 5 templates reached');
      return;
    }
    setTemplateActionError(null);
    setTemplateSaving(true);
    try {
      await onCreateTemplate(templateInput.trim());
      setTemplateInput('');
    } catch (error: any) {
      setTemplateActionError(error?.message || 'Unable to save template');
    } finally {
      setTemplateSaving(false);
    }
  };

  const handleTemplateDelete = async (templateId: number) => {
    setTemplateActionError(null);
    setDeletingTemplateId(templateId);
    try {
      await onDeleteTemplate(templateId);
    } catch (error: any) {
      setTemplateActionError(error?.message || 'Unable to delete template');
    } finally {
      setDeletingTemplateId(null);
    }
  };

  const handleTemplateClick = (text: string) => {
    setInput(text);
  };

  const activeSession = useMemo(() => sessions.find(s => s.id === activeSessionId), [sessions, activeSessionId]);
  const leadMetadata = activeSession?.metadata;
  const deviceLabel = leadMetadata?.device || leadMetadata?.browser || 'Unknown device';
  const cityLabel = leadMetadata?.city || leadMetadata?.location || 'Unknown city';

  const filteredSessions = useMemo(() => {
    return sessions.filter(s => {
      const matchesFilter = filter === 'ALL' || s.status === filter;
      const matchesSearch = s.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            s.lastMessage?.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [sessions, filter, searchTerm]);

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || !activeSessionId) return;
    onSendMessage(activeSessionId, input, isInternalMode);
    setInput('');
  };

  const [showSidebar, setShowSidebar] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(false);

  return (
    <div className="flex h-screen bg-white overflow-hidden relative">
      {/* Mobile Menu Button */}
      <button
        onClick={() => setShowSidebar(!showSidebar)}
        className="lg:hidden fixed top-4 left-4 z-50 bg-blue-600 text-white p-2 rounded-lg shadow-lg"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Navigator Column */}
      <div className={`${showSidebar ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:relative z-40 w-full sm:w-80 lg:w-80 h-full border-r border-gray-200 flex flex-col bg-gray-50/20 transition-transform duration-300`}>
        <div className="p-3 md:p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between mb-3 md:mb-4">
             <h1 className="text-lg md:text-xl font-black text-gray-900 tracking-tight">LeadPulse Agent</h1>
             <div className="flex items-center space-x-1 md:space-x-2">
               <div className="hidden md:block w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white"></div>
               {currentAgent?.role === 'SUPER_ADMIN' && (
                 <Link
                  to="/admin/super-admin"
                  className="text-[10px] md:text-xs bg-purple-100 text-purple-700 px-1.5 md:px-2 py-1 rounded hover:bg-purple-200 transition font-semibold"
                >
                  Admin
                </Link>
               )}
               {onLogout && (
                 <button
                  onClick={onLogout}
                  className="text-[10px] md:text-xs bg-red-100 text-red-700 px-1.5 md:px-2 py-1 rounded hover:bg-red-200 transition font-semibold"
                >
                  Logout
                </button>
               )}
             </div>
          </div>
          
          {currentAgent && <AgentShareLink agent={currentAgent} />}
          
          <input
            type="text"
            placeholder="Search active leads..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-100 border-none rounded-lg px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex border-b border-gray-200 bg-white text-[10px] font-bold uppercase tracking-wider text-gray-400">
          {(['OPEN', 'RESOLVED', 'ALL'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`flex-1 py-3 text-center transition-colors border-b-2 ${filter === f ? 'border-blue-600 text-blue-600' : 'border-transparent hover:text-gray-600'}`}
            >
              {f}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto">
          {filteredSessions.map(s => (
            <button
              key={s.id}
              onClick={() => onSelectSession(s.id)}
              className={`w-full p-4 flex items-start space-x-3 transition-all border-b border-gray-50 ${
                activeSessionId === s.id ? 'bg-blue-50 border-r-4 border-r-blue-600' : 'hover:bg-gray-50'
              }`}
            >
              <div className="relative">
                <img src={s.userAvatar} className="w-10 h-10 rounded-full border border-gray-200" alt="" />
                {s.status === 'OPEN' && <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-600 border-2 border-white rounded-full"></span>}
              </div>
              <div className="flex-1 text-left min-w-0">
                <div className="flex justify-between items-baseline">
                  <span className="font-bold text-gray-900 text-sm truncate">{s.userName}</span>
                  <span className="text-[10px] text-gray-400 shrink-0">
                    {new Date(s.updatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p className="text-xs text-gray-500 line-clamp-1 mt-0.5">{s.lastMessage}</p>
                <div className="mt-2">
                  <span className="text-[9px] bg-white border border-gray-200 text-gray-500 px-1.5 py-0.5 rounded uppercase font-bold tracking-tight">
                    {s.adSource?.split(' - ')[0]}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white" onClick={() => showSidebar && window.innerWidth < 1024 && setShowSidebar(false)}>
        {activeSession ? (
          <>
            <div className="px-3 md:px-6 py-3 md:py-4 border-b border-gray-200 flex items-center justify-between bg-white z-10">
              <div className="flex items-center space-x-2 md:space-x-3 min-w-0 flex-1">
                <div className="w-2 h-2 bg-green-500 rounded-full shrink-0"></div>
                <div className="min-w-0">
                  <h3 className="font-bold text-sm md:text-base text-gray-900 truncate">{activeSession.userName}</h3>
                  <p className="text-[10px] md:text-[11px] text-gray-400 truncate hidden sm:block">Campaign: {activeSession.adSource}</p>
                </div>
              </div>
              <div className="flex space-x-1 md:space-x-2 shrink-0">
                <button
                  onClick={() => setShowRightPanel(!showRightPanel)}
                  className="lg:hidden text-xs font-bold px-2 md:px-3 py-1.5 md:py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
                >
                  Info
                </button>
                {activeSession.status === 'OPEN' ? (
                  <button onClick={() => onUpdateStatus(activeSession.id, 'RESOLVED')} className="text-[10px] md:text-xs font-bold px-2 md:px-4 py-1.5 md:py-2 rounded-lg bg-gray-900 text-white hover:bg-black transition-all">Close</button>
                ) : (
                  <button onClick={() => onUpdateStatus(activeSession.id, 'OPEN')} className="text-[10px] md:text-xs font-bold px-2 md:px-4 py-1.5 md:py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50">Reopen</button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-3 md:p-6 bg-gray-50/20 no-scrollbar">
              {activeSession.messages.map(m => (
                <MessageBubble key={m.id} message={m} isMe={m.senderRole === 'AGENT'} />
              ))}
            </div>

            <div className="p-3 md:p-4 bg-white border-t border-gray-100">
              <div className="flex space-x-2 md:space-x-4 mb-2 md:mb-3">
                <button onClick={() => setIsInternalMode(false)} className={`text-[10px] font-black uppercase tracking-widest ${!isInternalMode ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-400'}`}>Reply to Client</button>
                <button onClick={() => setIsInternalMode(true)} className={`text-[10px] font-black uppercase tracking-widest ${isInternalMode ? 'text-amber-600 border-b-2 border-amber-600' : 'text-gray-400'}`}>Internal Note</button>
              </div>

              <form onSubmit={handleSend} className="flex flex-col space-y-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                  placeholder={isInternalMode ? "Agent notes (invisible to user)..." : "Type message..."}
                  className={`w-full border-none rounded-xl p-2 md:p-3 text-sm focus:ring-2 outline-none resize-none h-12 md:h-16 ${
                    isInternalMode ? 'bg-amber-50 focus:ring-amber-200 text-amber-900' : 'bg-gray-100 focus:ring-blue-200 text-gray-900'
                  }`}
                />
                <div className="flex justify-end">
                  <button type="submit" disabled={!input.trim()} className={`px-3 md:px-5 py-1.5 rounded-lg text-white font-bold text-[10px] md:text-xs flex items-center space-x-1 md:space-x-2 ${isInternalMode ? 'bg-amber-500' : 'bg-blue-600'}`}>
                    <span>Send</span>
                    <SendIcon className="w-3.5 h-3.5" />
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-300 italic text-sm">Select a lead to begin</div>
        )}
      </div>

      {/* Leads Detail Panel */}
      {activeSession && (
        <div className={`${showRightPanel ? 'block' : 'hidden'} lg:flex fixed lg:relative z-30 inset-x-0 bottom-0 lg:w-64 max-h-[70vh] lg:max-h-full border-t lg:border-t-0 lg:border-l border-gray-100 bg-white p-4 lg:p-5 flex-col overflow-y-auto`}>
          <div className="text-center mb-6">
            <img src={activeSession.userAvatar} className="w-16 h-16 rounded-xl mx-auto mb-3 border p-1" alt="" />
            <h4 className="font-bold text-gray-900 text-sm">{activeSession.userName}</h4>
          </div>
          <div className="space-y-6 flex-1">
            <div className="space-y-4">
              <p className="text-[10px] uppercase font-black text-gray-400 tracking-widest mb-1">Metadata</p>
              <div className="text-[11px] space-y-1">
                <div className="flex justify-between"><span className="text-gray-400">Status:</span> <span className="font-bold">{activeSession.status}</span></div>
                <div className="flex justify-between"><span className="text-gray-400">Campaign:</span> <span className="font-bold text-blue-600">{activeSession.adSource?.split(' - ')[0]}</span></div>
                <div className="flex justify-between"><span className="text-gray-400">Device:</span> <span className="font-semibold text-gray-900">{deviceLabel}</span></div>
                <div className="flex justify-between"><span className="text-gray-400">City:</span> <span className="font-semibold text-gray-900">{cityLabel}</span></div>
                <div className="flex justify-between"><span className="text-gray-400">IP:</span> <span>{activeSession.metadata?.ip || 'Unknown'}</span></div>
              </div>
              <button className="w-full py-2 bg-red-50 text-red-500 text-[10px] font-bold rounded-lg uppercase tracking-widest border border-red-100 hover:bg-red-100">Archive Lead</button>
            </div>
            <div className="border-t border-gray-100 pt-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] uppercase font-black text-gray-400 tracking-widest">Shared Templates</p>
                  <p className="text-[10px] text-gray-500">Click to inject a canned reply into the composer.</p>
                </div>
                <span className="text-[10px] uppercase tracking-widest text-gray-400">{templateList.length}/5 used</span>
              </div>
              <textarea
                value={templateInput}
                onChange={(e) => {
                  setTemplateInput(e.target.value);
                  setTemplateActionError(null);
                }}
                rows={3}
                placeholder="Draft a reusable reply..."
                className="w-full border border-gray-200 rounded-xl p-3 text-sm text-gray-800 focus:ring-2 focus:ring-blue-200 outline-none resize-none bg-gray-50"
              />
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={!templateInput.trim() || templateSaving || templateLimitReached}
                  onClick={handleTemplateSave}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition ${templateSaving ? 'bg-blue-400 text-white' : templateLimitReached ? 'bg-gray-200 text-gray-500' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
                >
                  {templateSaving ? 'Saving…' : 'Save template'}
                </button>
                <p className={`text-[10px] ${templateLimitReached ? 'text-red-500' : 'text-gray-400'}`}>
                  {templateLimitReached ? 'Maximum templates saved' : 'Shared across every agent'}
                </p>
              </div>
              {(templateActionError || templateLoadError) && (
                <p className="text-[10px] text-red-500">{templateActionError || templateLoadError}</p>
              )}
              {templatesLoading ? (
                <p className="text-[11px] text-gray-400">Loading templates…</p>
              ) : templateList.length === 0 ? (
                <p className="text-[11px] text-gray-400">No templates yet</p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {templateList.map((template) => (
                    <div key={template.id} className="flex items-center justify-between gap-2 bg-gray-50 border border-gray-100 rounded px-3 py-2">
                      <button
                        type="button"
                        onClick={() => handleTemplateClick(template.text)}
                        className="text-left text-sm text-gray-800 flex-1 truncate whitespace-pre-line"
                      >
                        {template.text}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTemplateDelete(template.id)}
                        disabled={deletingTemplateId === template.id}
                        className="text-[10px] font-semibold uppercase tracking-widest px-2 py-1 rounded border border-red-100 text-red-600 hover:bg-red-50 disabled:opacity-50"
                      >
                        {deletingTemplateId === template.id ? 'Removing' : 'Remove'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- Agent Share Link Component ---

const AgentShareLink: React.FC<{ agent: any }> = ({ agent }) => {
  const [copied, setCopied] = useState(false);
  const appUrl = window.location.origin;
  const referralLink = `${appUrl}/?ref_code=${agent.referral_code}`;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(referralLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-3 md:p-6 mb-3 md:mb-6">
      <div className="mb-3 md:mb-4">
        <h3 className="text-base md:text-lg font-bold text-gray-900 mb-1 md:mb-2">Your Referral Link</h3>
        <p className="text-xs md:text-sm text-gray-600 mb-2 md:mb-4">Share this link in your ads. Clients who click it will be assigned to you.</p>
      </div>
      
      <div className="bg-white border border-blue-200 rounded-lg p-2 md:p-4 mb-3 md:mb-4 flex items-center justify-between">
        <code className="text-xs md:text-sm text-blue-600 font-mono break-all">{referralLink}</code>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleCopyLink}
          className={`flex-1 py-2 px-4 rounded-lg font-bold text-sm uppercase tracking-widest transition-all ${
            copied
              ? 'bg-green-500 text-white'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {copied ? '✓ Copied!' : 'Copy Link'}
        </button>
      </div>

      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
        <strong>How to use:</strong> Copy this link and paste it into your Facebook ads, Google ads, or any other marketing material.
      </div>
    </div>
  );
};

// --- Agent Login Component ---

const AgentLogin: React.FC<{ onLoginSuccess: (agent: any) => void }> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await api.loginAgent(email, password);
      onLoginSuccess(result.agent);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-3 md:p-4">
      <div className="bg-white rounded-2xl shadow-xl p-5 md:p-8 w-full max-w-md">
        <div className="text-center mb-6 md:mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Agent Portal</h1>
          <p className="text-sm md:text-base text-gray-600">Sign in to access your dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 md:space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              placeholder="agent@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-3 rounded-lg transition duration-200 flex items-center justify-center"
          >
            {loading ? (
              <span>Signing in...</span>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Demo: Use credentials from agent registration</p>
        </div>
      </div>
    </div>
  );
};

// --- App Orchestration ---

const App: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>(INITIAL_SESSIONS);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentAgent, setCurrentAgent] = useState<any>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [templates, setTemplates] = useState<api.MessageTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [templateLoadError, setTemplateLoadError] = useState<string | null>(null);
  const offlineNoticeText = "Thank you for reaching out. We'll assign someone to guide you as soon as we can.";

  const ensureOfflineNotice = useCallback((sessionId: string) => {
    setSessions(prev => prev.map(session => {
      if (session.id !== sessionId) return session;
      if (session.offlineNotified) return session;
      const hasAgentReply = session.messages.some(m => m.senderRole === 'AGENT' && !m.isInternal);
      if (hasAgentReply) {
        return { ...session, offlineNotified: true };
      }
      const notice: Message = {
        id: `auto-${Date.now()}`,
        senderId: 'system',
        senderRole: 'AGENT',
        text: offlineNoticeText,
        timestamp: Date.now(),
        status: 'sent'
      };
      return {
        ...session,
        offlineNotified: true,
        messages: [...session.messages, notice],
        lastMessage: notice.text,
        updatedAt: notice.timestamp
      };
    }));
  }, [offlineNoticeText]);

  // Check for existing auth token on mount
  useEffect(() => {
    const token = api.getAuthToken();
    if (token) {
      api.getCurrentAgent()
        .then(agent => {
          setCurrentAgent(agent);
          setIsAuthenticated(true);
          console.log('✅ Auth restored from token:', agent.email);
        })
        .catch((error) => {
          console.error('❌ Auth token validation failed:', error.message);
          api.clearAuthToken();
        });
    } else {
      console.log('ℹ️ No auth token found on mount');
    }
  }, []);

  const handleLoginSuccess = (agent: any) => {
    setCurrentAgent(agent);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    api.clearAuthToken();
    setCurrentAgent(null);
    setIsAuthenticated(false);
  };

  const handleSessionExpired = () => {
    alert('Your session has ended because you logged in from another device.');
    handleLogout();
  };

  const fetchTemplates = useCallback(async () => {
    setTemplateLoadError(null);
    setTemplatesLoading(true);
    try {
      const list = await api.listMessageTemplates();
      setTemplates(list);
    } catch (error: any) {
      setTemplateLoadError(error?.message || 'Unable to load templates');
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && currentAgent) {
      fetchTemplates();
    } else {
      setTemplates([]);
      setTemplateLoadError(null);
      setTemplatesLoading(false);
    }
  }, [isAuthenticated, currentAgent, fetchTemplates]);

  const handleCreateTemplate = useCallback(async (text: string) => {
    await api.createMessageTemplate(text);
    await fetchTemplates();
  }, [fetchTemplates]);

  const handleDeleteTemplate = useCallback(async (templateId: number) => {
    await api.deleteMessageTemplate(templateId);
    await fetchTemplates();
  }, [fetchTemplates]);

  // Simulation: Persist to localStorage for now (Agent in VS Code will replace this with Python API calls)
  useEffect(() => {
    const saved = localStorage.getItem('leadpulse_v2');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Only load backend sessions (already synced from API)
        // Local-only sessions might be stale from old testing
        const backendOnly = parsed.filter((s: any) => s.id.includes('backend-'));
        setSessions(backendOnly);
      } catch (e) {
        console.warn('Failed to parse stored sessions:', e);
      }
    }
  }, []);

  useEffect(() => {
    // Only persist backend sessions (local-only sessions will be recreated from API)
    const backendSessions = sessions.filter(s => s.id.includes('backend-'));
    localStorage.setItem('leadpulse_v2', JSON.stringify(backendSessions));
  }, [sessions]);

  // Load initial sessions from backend API and setup WebSocket
  useEffect(() => {
    // Only load backend sessions if authenticated
    if (!isAuthenticated || !currentAgent) {
      return;
    }

    const loadBackendSessions = async () => {
      try {
        const backendSessions = await api.listSessions();
        if (!backendSessions || !Array.isArray(backendSessions)) {
          // Invalid response from backend API
          return;
        }
        
        if (backendSessions.length > 0) {
          // Convert backend sessions to app format
          const convertedSessions = backendSessions
            .filter(bs => bs && bs.id) // Filter out invalid sessions
            .map(bs => ({
              id: `backend-${bs.id}`,
              userId: bs.user_id || 'unknown',
              userName: bs.user_name || 'Unknown User',
              userAvatar: bs.user_avatar || 'https://picsum.photos/seed/user/200',
              lastMessage: bs.messages && bs.messages.length > 0 
                ? bs.messages[bs.messages.length - 1].text 
                : 'No messages',
              updatedAt: bs.updated_at ? new Date(bs.updated_at).getTime() : Date.now(),
              status: bs.status === 'OPEN' ? 'OPEN' : 'RESOLVED',
              messages: (bs.messages || []).map(m => ({
                id: `m-${m.id}`,
                senderId: m.sender_id || 'unknown',
                senderRole: (m.sender_role as Role) || 'USER',
                text: m.text || '',
                timestamp: m.timestamp ? new Date(m.timestamp).getTime() : Date.now(),
                status: 'sent' as any,
                isInternal: m.is_internal || false
              })),
              adSource: bs.ad_source || 'Unknown',
              unreadCount: 0,
              metadata: bs.lead_metadata ? {
                browser: bs.lead_metadata.browser,
                ip: bs.lead_metadata.ip,
                location: bs.lead_metadata.location,
                city: bs.lead_metadata.city,
                device: bs.lead_metadata.device,
                adId: bs.lead_metadata.ad_id
              } : undefined
            }));
          
          // Merge with existing backend sessions (deduplicate by user_id to prevent duplicates)
          setSessions(prev => {
            const existing = prev.filter(s => !s.id.includes('backend-'));
            const existingUserIds = new Set(existing.map(s => s.userId));
            const uniqueConverted = convertedSessions.filter(s => !existingUserIds.has(s.userId));
            return [...existing, ...uniqueConverted];
          });
        }
      } catch (error) {
        // Could not load sessions from backend API
        // Continue with local sessions only
      }
    };
    
    // Load backend sessions when authenticated
    loadBackendSessions();
  }, [isAuthenticated, currentAgent]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!isAuthenticated || !currentAgent) {
      if (ws) {
        ws.close();
        setWs(null);
      }
      return;
    }

    // Establish WebSocket connection
    const token = api.getAuthToken();
    const rawApiUrl = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
    let wsBase: string;

    if (rawApiUrl) {
      const normalizedApiUrl = rawApiUrl.endsWith('/api') ? rawApiUrl : `${rawApiUrl}/api`;
      wsBase = normalizedApiUrl.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:');
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsBase = `${protocol}//${window.location.host}/api`;
    }

    const wsUrl = token
      ? `${wsBase}/ws?token=${encodeURIComponent(token)}`
      : `${wsBase}/ws`;
    
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      // WebSocket connected, agent subscribed
      // Subscribe to agent updates
      websocket.send(JSON.stringify({
        type: 'subscribe',
        agent_id: currentAgent.id
      }));
      setWs(websocket);
    };
    
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // WebSocket message received
        
        if (data.type === 'message') {
          const messageData = data.data;
          const backendSessionId = messageData.session_id;
          const sessionId = `backend-${backendSessionId}`;
          
          // Adding message to session
          
          // Store in localStorage to trigger other tabs
          localStorage.setItem('ws_message', JSON.stringify({
            sessionId,
            messageData,
            timestamp: Date.now()
          }));
          
          // Add or update message in the session
          setSessions(prev => prev.map(session => {
            if (session.id === sessionId) {
              const newMessage: Message = {
                id: `m-${messageData.id}`,
                senderId: messageData.sender_id,
                senderRole: messageData.sender_role as Role,
                text: messageData.text,
                timestamp: new Date(messageData.timestamp).getTime(),
                status: 'sent',
                isInternal: messageData.is_internal || false
              };
              // Message added to session
              return {
                ...session,
                messages: [...session.messages, newMessage],
                lastMessage: newMessage.text,
                updatedAt: Date.now(),
                unreadCount: session.id === currentSessionId ? 0 : session.unreadCount + 1
              };
            }
            return session;
          }));
        } else if (data.type === 'session_created') {
          // New session created, fetch it from backend
          // New session created, reloading
          loadBackendSessions();
        }
      } catch (error) {
        // Error processing WebSocket message
      }
    };
    
    websocket.onerror = (error) => {
      // WebSocket error
    };
    
    websocket.onclose = () => {
      // WebSocket disconnected
      setWs(null);
    };
    
    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, [isAuthenticated, currentAgent, currentSessionId]);

  // Cross-tab message sync listener
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'ws_message' && e.newValue) {
        try {
          const data = JSON.parse(e.newValue);
          const { sessionId, messageData } = data;
          
          // Storage event: syncing message from another tab
          
          // Add message to current tab
          setSessions(prev => prev.map(session => {
            if (session.id === sessionId) {
              const newMessage: Message = {
                id: `m-${messageData.id}`,
                senderId: messageData.sender_id,
                senderRole: messageData.sender_role as Role,
                text: messageData.text,
                timestamp: new Date(messageData.timestamp).getTime(),
                status: 'sent',
                isInternal: messageData.is_internal || false
              };
              return {
                ...session,
                messages: [...session.messages, newMessage],
                lastMessage: newMessage.text,
                updatedAt: Date.now(),
                unreadCount: session.id === currentSessionId ? 0 : session.unreadCount + 1
              };
            }
            return session;
          }));
        } catch (error) {
          // Error processing cross-tab message
        }
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [currentSessionId]);

  // Fallback database fetch every 30 seconds
  useEffect(() => {
    if (!isAuthenticated || !currentAgent) return;
    
    const fetchSessions = async () => {
      try {
        const backendSessions = await api.listSessions();
        if (!backendSessions || !Array.isArray(backendSessions)) {
          return;
        }
        
        if (backendSessions.length > 0) {
          const convertedSessions = backendSessions
            .filter(bs => bs && bs.id)
            .map(bs => ({
              id: `backend-${bs.id}`,
              userId: bs.user_id || 'unknown',
              userName: bs.user_name || 'Unknown User',
              userAvatar: bs.user_avatar || 'https://picsum.photos/seed/user/200',
              lastMessage: bs.messages && bs.messages.length > 0 
                ? bs.messages[bs.messages.length - 1].text 
                : 'No messages',
              updatedAt: bs.updated_at ? new Date(bs.updated_at).getTime() : Date.now(),
              status: bs.status === 'OPEN' ? 'OPEN' : 'RESOLVED',
              messages: (bs.messages || []).map(m => ({
                id: `m-${m.id}`,
                senderId: m.sender_id || 'unknown',
                senderRole: (m.sender_role as Role) || 'USER',
                text: m.text || '',
                timestamp: m.timestamp ? new Date(m.timestamp).getTime() : Date.now(),
                status: 'sent' as any,
                isInternal: m.is_internal || false
              })),
              adSource: bs.ad_source || 'Unknown',
              unreadCount: 0,
              metadata: bs.lead_metadata ? {
                browser: bs.lead_metadata.browser,
                ip: bs.lead_metadata.ip,
                location: bs.lead_metadata.location,
                city: bs.lead_metadata.city,
                device: bs.lead_metadata.device,
                adId: bs.lead_metadata.ad_id
              } : undefined
            }));
          
          // Update sessions (keep local ones, update backend ones)
          setSessions(prev => {
            const existing = prev.filter(s => !s.id.includes('backend-'));
            return [...existing, ...convertedSessions];
          });
        }
      } catch (error: any) {
        // Check if this is a session expired error
        if (error?.status === 401 || error?.message?.includes("Session expired")) {
          handleSessionExpired();
          return;
        }
        // Fallback database fetch failed
      }
    };
    
    // Fetch immediately, then every 30 seconds
    fetchSessions();
    const interval = setInterval(fetchSessions, 30000);
    
    return () => clearInterval(interval);
  }, [isAuthenticated, currentAgent]);

  const loadBackendSessions = async () => {
    try {
      const backendSessions = await api.listSessions();
      if (!backendSessions || !Array.isArray(backendSessions)) {
        return;
      }
      
      if (backendSessions.length > 0) {
        const convertedSessions = backendSessions
          .filter(bs => bs && bs.id)
          .map(bs => ({
            id: `backend-${bs.id}`,
            userId: bs.user_id || 'unknown',
            userName: bs.user_name || 'Unknown User',
            userAvatar: bs.user_avatar || 'https://picsum.photos/seed/user/200',
            lastMessage: bs.messages && bs.messages.length > 0 
              ? bs.messages[bs.messages.length - 1].text 
              : 'No messages',
            updatedAt: bs.updated_at ? new Date(bs.updated_at).getTime() : Date.now(),
            status: bs.status === 'OPEN' ? 'OPEN' : 'RESOLVED',
            messages: (bs.messages || []).map(m => ({
              id: `m-${m.id}`,
              senderId: m.sender_id || 'unknown',
              senderRole: (m.sender_role as Role) || 'USER',
              text: m.text || '',
              timestamp: m.timestamp ? new Date(m.timestamp).getTime() : Date.now(),
              status: 'sent' as any,
              isInternal: m.is_internal || false
            })),
            adSource: bs.ad_source || 'Unknown',
            unreadCount: 0,
              metadata: bs.lead_metadata ? {
                browser: bs.lead_metadata.browser,
                ip: bs.lead_metadata.ip,
                location: bs.lead_metadata.location,
                city: bs.lead_metadata.city,
                device: bs.lead_metadata.device,
                adId: bs.lead_metadata.ad_id
              } : undefined
          }));
        
        setSessions(prev => {
          const existing = prev.filter(s => !s.id.includes('backend-'));
          return [...existing, ...convertedSessions];
        });
      }
    } catch (error) {
      // Could not load sessions
    }
  };

  const handleUserSendMessage = useCallback(async (text: string) => {
    // Use currentSessionId from state for accurate session tracking
    if (!currentSessionId) {
      return;
      return;
    }

    // Find the current session so we can use its userId
    const currentSession = sessions.find(s => s.id === currentSessionId);
    if (!currentSession) {
      return;
      return;
    }

    const newMessage: Message = { id: `m-${Date.now()}`, senderId: currentSession.userId, senderRole: 'USER', text, timestamp: Date.now(), status: 'sent' };
    
    // Update local state
    setSessions(prev => prev.map(s => s.id === currentSessionId ? { ...s, lastMessage: text, updatedAt: Date.now(), messages: [...s.messages, newMessage], unreadCount: s.unreadCount + 1 } : s));

    // If no agent has responded yet, add a reassuring offline notice locally
    ensureOfflineNotice(currentSessionId);
    
    // Send to backend API if it's a backend session
    if (currentSessionId.includes('backend-')) {
      try {
        const backendSessionId = parseInt(currentSessionId.split('-')[1]);
        if (isNaN(backendSessionId)) {
          return;
          return;
        }
        await api.sendMessage(backendSessionId, currentSession.userId, 'USER', text, false);
      } catch (error: any) {
        if (error?.status === 401 || error?.message?.includes("Session expired")) {
          handleSessionExpired();
          return;
        }
        return;
        // Optionally show user-friendly error message
      }
    }
  }, [sessions, currentSessionId, ensureOfflineNotice]);

  const handleAgentSendMessage = useCallback((sessionId: string, text: string, isInternal: boolean = false) => {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) {
      return;
      return;
    }
    
    const agentId = currentAgent?.id?.toString() || 'agent-unknown';
    const newMessage: Message = { id: `m-${Date.now()}`, senderId: agentId, senderRole: 'AGENT', text, timestamp: Date.now(), status: 'sent', isInternal };
    setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, lastMessage: isInternal ? s.lastMessage : text, updatedAt: Date.now(), messages: [...s.messages, newMessage], unreadCount: 0 } : s));

    // Broadcast to other tabs (including client tabs) via localStorage sync
    localStorage.setItem('ws_message', JSON.stringify({
      sessionId,
      messageData: {
        id: newMessage.id,
        sender_id: newMessage.senderId,
        sender_role: 'AGENT',
        text: newMessage.text,
        timestamp: new Date(newMessage.timestamp).toISOString(),
        is_internal: newMessage.isInternal
      },
      timestamp: Date.now()
    }));
    
    // Send to backend API if it's a backend session
    if (sessionId.includes('backend-')) {
      try {
        const backendSessionId = parseInt(sessionId.split('-')[1]);
        if (isNaN(backendSessionId)) {
          return;
        }
        api.sendMessage(backendSessionId, agentId, 'AGENT', text, isInternal).catch(err => {
          // Optionally revert the local state update on error
        });
      } catch (error) {
        // Error sending message silently caught
      }
    }
  }, [sessions, currentAgent]);

  const handleUpdateStatus = useCallback((sessionId: string, status: SessionStatus) => {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) {
      return;
    }
    
    // Update local state optimistically
    setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, status } : s));
    
    // Update in backend API if it's a backend session
    if (sessionId.includes('backend-')) {
      try {
        const backendSessionId = parseInt(sessionId.split('-')[1]);
        if (isNaN(backendSessionId)) {
          // Revert the status change
          setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, status: session.status } : s));
          return;
        }
        api.updateSession(backendSessionId, { 
          status: status === 'OPEN' ? 'OPEN' : 'RESOLVED' 
        }).catch(err => {
          // Revert the status change on error
          setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, status: session.status } : s));
        });
      } catch (error) {
        // Revert the status change on error
        setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, status: session.status } : s));
      }
    }
  }, [sessions]);

  const selectSession = (id: string) => {
    setCurrentSessionId(id);
    setSessions(prev => prev.map(s => s.id === id ? { ...s, unreadCount: 0 } : s));
  };

  // Make handleLogout available to components
  useEffect(() => {
    (window as any).handleLogout = handleLogout;
  }, []);

  const UserLanding = () => {
    const location = useLocation();
    // HashRouter keeps query params after the #; support both styles
    const rawQuery = location.search || location.hash.split('?')[1] || '';
    const query = new URLSearchParams(rawQuery);
    const adSource = query.get('ref') || AD_SOURCES[0];
    const referralCode = query.get('ref_code') || query.get('referral_code') || undefined;
    const cityQuery = query.get('city')?.trim();
    const inferredCity = cityQuery || 'Unknown City';
    const deviceInfo = typeof navigator !== 'undefined' ? navigator.userAgent : 'Browser';
    const [backendSessionId, setBackendSessionId] = useState<number | null>(null);
    
    // Generate unique client ID per tab (using sessionStorage, not shared across tabs)
    // Each tab gets its own ID, so opening same link in new tab = fresh session
    // Refreshing same tab keeps existing sessionStorage ID = same conversation
    const [clientId] = useState(() => {
      let id = sessionStorage.getItem('leadpulse_client_id');
      if (!id) {
        id = `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        sessionStorage.setItem('leadpulse_client_id', id);
      }
      return id;
    });

    // Validate referral code - required to access client portal
    if (!referralCode) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
          <div className="text-center p-8 max-w-md bg-white rounded-lg shadow">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Invalid Access</h1>
            <p className="text-gray-600">This page requires a valid referral link from your agent. Please contact your agent for access.</p>
          </div>
        </div>
      );
    }

    useEffect(() => {
      // Prevent duplicate session creation by checking if session already exists
      const existingSession = sessions.find(s => 
        (s.id.includes('backend-') && s.userId === clientId) || 
        s.id === `user-session-${clientId}`
      );
      if (existingSession) {
        setBackendSessionId(
          existingSession.id.includes('backend-') 
            ? parseInt(existingSession.id.split('-')[1]) 
            : null
        );
        setCurrentSessionId(existingSession.id);
        return; // Don't create duplicate
      }

      // Create session in backend API
      const createBackendSession = async () => {
        try {
          const backendSession = await api.createSession(
            clientId,
            'Lead Candidate',
            adSource,
            'https://picsum.photos/seed/lead/200',
            referralCode,
            {
              ip: 'Client IP',
              location: inferredCity,
              city: inferredCity,
              browser: 'Client Web Application',
              device: deviceInfo,
              ad_id: query.get('ad_id') || 'REF_LINK'
            }
          );
          setBackendSessionId(backendSession.id);
          
          // Add backend session to state
          const newSession: ChatSession = {
            id: `backend-${backendSession.id}`,
            userId: backendSession.user_id,
            userName: backendSession.user_name,
            userAvatar: backendSession.user_avatar,
            lastMessage: 'Session created',
            updatedAt: new Date(backendSession.created_at).getTime(),
            status: backendSession.status === 'OPEN' ? 'OPEN' : 'RESOLVED',
            messages: [],
            adSource: backendSession.ad_source,
            unreadCount: 0,
            metadata: backendSession.lead_metadata ? {
              browser: backendSession.lead_metadata.browser,
              ip: backendSession.lead_metadata.ip,
              location: backendSession.lead_metadata.location,
              city: backendSession.lead_metadata.city,
              device: backendSession.lead_metadata.device,
              adId: backendSession.lead_metadata.ad_id
            } : undefined
          };
          setSessions(prev => [...prev, newSession]);
          setCurrentSessionId(`backend-${backendSession.id}`);
          
          // Load existing messages (like auto-welcome)
          try {
            const messages = await api.getSessionMessages(backendSession.id);
            if (messages && messages.length > 0) {
              setSessions(prev => prev.map(s => 
                s.id === `backend-${backendSession.id}`
                  ? {
                      ...s,
                      messages: messages.map(m => ({
                        id: `m-${m.id}`,
                        senderId: m.sender_id,
                        senderRole: m.sender_role as Role,
                        text: m.text,
                        timestamp: new Date(m.timestamp).getTime(),
                        status: 'sent' as any,
                        isInternal: m.is_internal || false
                      })),
                      lastMessage: messages[messages.length - 1]?.text || 'Session created'
                    }
                  : s
              ));
            }
          } catch (error) {
            // Failed to load messages, continue without them
          }
        } catch (error) {
          // Fallback to local session
          if (!sessions.find(s => s.id === `user-session-${clientId}`)) {
            const newSession: ChatSession = {
              id: `user-session-${clientId}`, userId: clientId, userName: 'Lead Candidate', 
              userAvatar: `https://picsum.photos/seed/lead/200`,
              lastMessage: 'Interested in the promotion', updatedAt: Date.now(),
              status: 'OPEN', messages: [], adSource, unreadCount: 0,
              metadata: { browser: 'Client Web Application', ip: 'Mock Client IP', adId: query.get('ad_id') || 'REF_LINK', location: inferredCity, city: inferredCity, device: deviceInfo }
            };
            setSessions(prev => [...prev, newSession]);
            // Set currentSessionId in parent
            setCurrentSessionId(`user-session-${clientId}`);
          }
        }
      };
      
      // Call createBackendSession
      createBackendSession();
    }, [sessions, clientId, currentSessionId, adSource, referralCode, inferredCity, deviceInfo, query]);

    const s = sessions.find(s => s.id === `backend-${backendSessionId}`) || sessions.find(s => s.id === `user-session-${clientId}`);
    return s ? <UserChatView session={s} onSendMessage={handleUserSendMessage} /> : <div className="p-10 text-center">Loading portal...</div>;
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-white">
        <Routes>
          <Route path="/" element={<UserLanding />} />
          <Route path="/login" element={
            isAuthenticated ? <Navigate to="/admin" replace /> : <AgentLogin onLoginSuccess={handleLoginSuccess} />
          } />
          <Route path="/admin" element={
            isAuthenticated ? (
              <AdminDashboard 
                sessions={sessions} 
                activeSessionId={currentSessionId}
                onSelectSession={selectSession}
                onSendMessage={handleAgentSendMessage}
                onUpdateStatus={handleUpdateStatus}
                currentAgent={currentAgent}
                onLogout={handleLogout}
                templates={templates}
                templatesLoading={templatesLoading}
                templateLoadError={templateLoadError}
                onCreateTemplate={handleCreateTemplate}
                onDeleteTemplate={handleDeleteTemplate}
              />
            ) : (
              <Navigate to="/login" replace />
            )
          } />
          <Route path="/admin/super-admin" element={
            isAuthenticated && currentAgent?.role === 'SUPER_ADMIN' ? (
              <SuperAdminDashboard />
            ) : isAuthenticated ? (
              <div className="min-h-screen flex items-center justify-center text-gray-500">Unauthorized - Super Admin access only</div>
            ) : (
              <Navigate to="/login" replace />
            )
          } />
          <Route path="*" element={<Navigate to={isAuthenticated ? "/admin" : "/login"} replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
};

export default App;
