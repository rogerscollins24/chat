import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  adminListAgents,
  adminCreateAgent,
  adminUpdateAgent,
  adminDeleteAgent,
  adminRotateReferral,
  adminResetPassword,
  adminListSessions,
  adminReassignSession,
  adminExportSessions,
  getOverflowAgents,
  reassignSessions,
  clearAuthToken,
  Agent,
  Session,
  OverflowAgent,
} from '../src/services/api';

const SuperAdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [overflowAgents, setOverflowAgents] = useState<OverflowAgent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filterAgentId, setFilterAgentId] = useState<number | 'ALL'>('ALL');
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ email: '', name: '', password: '', role: 'AGENT', is_default_pool: false });
  const [resetPwd, setResetPwd] = useState('');
  const [reassignModal, setReassignModal] = useState<{ fromAgentId: number; fromAgentName: string } | null>(null);
  const [selectedTargetAgent, setSelectedTargetAgent] = useState<number | null>(null);
  const [reassigning, setReassigning] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);

  const handleLogout = () => {
    clearAuthToken();
    navigate('/admin');
    window.location.reload();
  };

  const handleBackToAdmin = () => {
    navigate('/admin');
  };

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [a, s, o] = await Promise.all([
        adminListAgents(),
        adminListSessions({ limit: 200 }),
        getOverflowAgents(),
      ]);
      setAgents(a);
      setSessions(s);
      setOverflowAgents(o.agents);
    } catch (e: any) {
      setError(e.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredSessions = useMemo(() => {
    if (filterAgentId === 'ALL') return sessions;
    return sessions.filter(s => s.assigned_agent_id === filterAgentId);
  }, [sessions, filterAgentId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError('');
    try {
      await adminCreateAgent(form);
      setForm({ email: '', name: '', password: '', role: 'AGENT', is_default_pool: false });
      loadData();
    } catch (e: any) {
      setError(e.message || 'Create failed');
    } finally {
      setCreating(false);
    }
  };

  const handleReassign = async (sessionId: number, agentId: number) => {
    await adminReassignSession(sessionId, agentId);
    loadData();
  };

  const handleExport = async () => {
    const res = await adminExportSessions(filterAgentId === 'ALL' ? {} : { agent_id: filterAgentId as number });
    const blob = new Blob([JSON.stringify(res, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sessions-export.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleReassignBulk = async () => {
    if (!reassignModal || !selectedTargetAgent) return;
    setReassigning(true);
    setError('');
    try {
      await reassignSessions(reassignModal.fromAgentId, selectedTargetAgent);
      setReassignModal(null);
      setSelectedTargetAgent(null);
      loadData();
    } catch (e: any) {
      setError(e.message || 'Reassignment failed');
    } finally {
      setReassigning(false);
    }
  };

  return (
    <div className="h-screen bg-gray-50 flex overflow-hidden relative">
      {/* Mobile Menu Button */}
      <button
        onClick={() => setShowSidebar(!showSidebar)}
        className="lg:hidden fixed top-4 left-4 z-50 bg-purple-600 text-white p-2 rounded-lg shadow-lg"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div className={`${showSidebar ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:relative z-40 w-full sm:w-80 lg:w-80 h-full border-r bg-white p-3 md:p-4 space-y-3 md:space-y-4 overflow-y-auto transition-transform duration-300`}>
        <div className="flex items-center justify-between mb-3 md:mb-4">
          <h2 className="text-lg md:text-xl font-bold">Super Admin</h2>
          <button
            onClick={handleBackToAdmin}
            className="px-2 md:px-3 py-1 text-xs md:text-sm border rounded hover:bg-gray-100"
            title="Back to agent dashboard"
          >
            ← Back
          </button>
        </div>
        {error && <div className="text-red-600 text-xs md:text-sm">{error}</div>}
        <div className="flex gap-1 md:gap-2">
          <button
            onClick={loadData}
            className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-xs md:text-sm font-semibold hover:bg-blue-700"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button
            onClick={handleLogout}
            className="flex-1 bg-red-600 text-white py-2 rounded-lg text-xs md:text-sm font-semibold hover:bg-red-700"
            title="Logout"
          >
            Logout
          </button>
        </div>

        <div className="space-y-2">
          <h3 className="text-xs md:text-sm font-semibold text-gray-700">Filter by Agent</h3>
          <select
            className="w-full border rounded px-2 py-2 text-xs md:text-sm"
            value={filterAgentId}
            onChange={(e) => setFilterAgentId(e.target.value === 'ALL' ? 'ALL' : Number(e.target.value))}
          >
            <option value="ALL">All</option>
            {agents.map(a => (
              <option key={a.id} value={a.id}>{a.name} ({a.role || 'AGENT'})</option>
            ))}
          </select>
          <button
            onClick={handleExport}
            className="w-full bg-emerald-600 text-white py-2 rounded-lg text-xs md:text-sm font-semibold hover:bg-emerald-700"
          >
            Export JSON
          </button>
        </div>

        <div className="border-t pt-3 md:pt-4">
          <h3 className="text-xs md:text-sm font-semibold text-gray-700 mb-2">Create Agent</h3>
          <form onSubmit={handleCreate} className="space-y-2 text-xs md:text-sm">
            <input className="w-full border rounded px-2 py-2" placeholder="Email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
            <input className="w-full border rounded px-2 py-2" placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
            <div>
              <input className="w-full border rounded px-2 py-2" placeholder="Password (min 8 chars)" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
              <div className="mt-1 text-xs text-gray-600 space-y-0.5">
                <div>Password must have:</div>
                <div className={form.password.length >= 8 ? 'text-green-600' : 'text-gray-500'}>✓ At least 8 characters</div>
                <div className={/[A-Z]/.test(form.password) ? 'text-green-600' : 'text-gray-500'}>✓ At least 1 UPPERCASE letter</div>
                <div className={/[a-z]/.test(form.password) ? 'text-green-600' : 'text-gray-500'}>✓ At least 1 lowercase letter</div>
                <div className={/[0-9]/.test(form.password) ? 'text-green-600' : 'text-gray-500'}>✓ At least 1 number (0-9)</div>
              </div>
            </div>
            <select className="w-full border rounded px-2 py-2" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
              <option value="AGENT">Agent</option>
              <option value="SUPER_ADMIN">Super Admin</option>
            </select>
            <label className="flex items-center space-x-2 text-xs">
              <input type="checkbox" checked={form.is_default_pool} onChange={e => setForm({ ...form, is_default_pool: e.target.checked })} />
              <span>Set as default pool</span>
            </label>
            <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700" disabled={creating}>{creating ? 'Creating...' : 'Create'}</button>
          </form>
        </div>
      </div>

      <div className="flex-1 p-3 md:p-6 space-y-4 md:space-y-6 overflow-auto" onClick={() => showSidebar && window.innerWidth < 1024 && setShowSidebar(false)}>
        <div className="bg-white rounded-xl shadow p-3 md:p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-base md:text-lg">⚠️ Overflow Agents (50+ leads/24h)</h3>
          </div>
          {overflowAgents.filter(a => a.is_overflowed).length === 0 ? (
            <div className="text-xs md:text-sm text-gray-500 py-2">No agents in overflow</div>
          ) : (
            <div className="divide-y">
              {overflowAgents.filter(a => a.is_overflowed).map(agent => (
                <div key={agent.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-sm text-orange-600">{agent.name}</div>
                    <div className="text-xs text-gray-500">{agent.session_count_24h} sessions in 24h</div>
                  </div>
                  <button
                    className="px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700"
                    onClick={() => {
                      setReassignModal({ fromAgentId: agent.id, fromAgentName: agent.name });
                      setSelectedTargetAgent(null);
                    }}
                  >
                    Reassign Overflow
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {reassignModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl p-4 md:p-6 w-full max-w-md">
              <h3 className="text-lg font-bold mb-4">Reassign Sessions from {reassignModal.fromAgentName}</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2">Select Target Agent</label>
                  <select
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={selectedTargetAgent || ''}
                    onChange={(e) => setSelectedTargetAgent(Number(e.target.value))}
                  >
                    <option value="">-- Choose agent --</option>
                    {agents
                      .filter(a => a.id !== reassignModal.fromAgentId)
                      .map(a => (
                        <option key={a.id} value={a.id}>
                          {a.name} ({overflowAgents.find(oa => oa.id === a.id)?.session_count_24h || 0} sessions)
                        </option>
                      ))}
                  </select>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded p-3 text-xs text-blue-700">
                  All open sessions from the last 24 hours will be reassigned to the target agent.
                </div>
                <div className="flex gap-2">
                  <button
                    className="flex-1 px-4 py-2 bg-orange-600 text-white text-sm rounded hover:bg-orange-700 disabled:bg-gray-400"
                    onClick={handleReassignBulk}
                    disabled={!selectedTargetAgent || reassigning}
                  >
                    {reassigning ? 'Reassigning...' : 'Confirm Reassign'}
                  </button>
                  <button
                    className="flex-1 px-4 py-2 border text-sm rounded hover:bg-gray-50"
                    onClick={() => {
                      setReassignModal(null);
                      setSelectedTargetAgent(null);
                    }}
                    disabled={reassigning}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl shadow p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-lg">Agents</h3>
          </div>
          <div className="divide-y">
            {agents.map(agent => (
              <div key={agent.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm">{agent.name} ({agent.email})</div>
                  <div className="text-xs text-gray-500">Role: {agent.role || 'AGENT'} · Referral: {agent.referral_code}</div>
                </div>
                <div className="flex gap-2 text-xs">
                  <button className="px-3 py-1 border rounded" onClick={() => adminRotateReferral(agent.id).then(loadData)}>Rotate Referral</button>
                  <button className="px-3 py-1 border rounded" onClick={() => resetPwd && adminResetPassword(agent.id, resetPwd).then(() => setResetPwd(''))}>Reset Pwd</button>
                  <button className="px-3 py-1 border rounded text-red-600" onClick={() => adminDeleteAgent(agent.id).then(loadData)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-2 text-xs text-gray-500">Set new password then click Reset Pwd:</div>
          <input className="mt-1 border rounded px-2 py-1 text-sm" placeholder="New password" value={resetPwd} onChange={e => setResetPwd(e.target.value)} />
        </div>

        <div className="bg-white rounded-xl shadow p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-base md:text-lg">Sessions ({filteredSessions.length})</h3>
          </div>
          <div className="divide-y overflow-x-auto">
            {filteredSessions.map(s => (
              <div key={s.id} className="py-3 text-xs md:text-sm">
                <div className="flex flex-col md:flex-row justify-between md:items-center gap-2">
                  <div className="flex-1">
                    <div className="font-semibold">{s.user_name} · #{s.id}</div>
                    <div className="text-gray-500 text-xs">Assigned: {s.assigned_agent_id || 'Unassigned'} · Status: {s.status}</div>
                    {s.lead_metadata && (
                      <div className="text-gray-600 text-xs mt-1 space-y-0.5">
                        {s.lead_metadata.browser && <div>Browser: {s.lead_metadata.browser}</div>}
                        {s.lead_metadata.device && <div>Device: {s.lead_metadata.device}</div>}
                        {s.lead_metadata.location && <div>Location: {s.lead_metadata.location}</div>}
                        {s.lead_metadata.ip && <div>IP: {s.lead_metadata.ip}</div>}
                      </div>
                    )}
                  </div>
                  <select
                    className="border rounded px-2 py-1 text-xs w-full md:w-auto"
                    value={s.assigned_agent_id || ''}
                    onChange={(e) => handleReassign(s.id, Number(e.target.value))}
                  >
                    <option value="">Unassigned</option>
                    {agents.map(a => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuperAdminDashboard;
