import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { CompressionSession, PaginatedResponse, StatsSummary } from '../types';
import { SessionList } from './SessionList';
import { CreateSessionForm } from './CreateSessionForm';

export function Dashboard() {
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [sessions, setSessions] = useState<PaginatedResponse<CompressionSession> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const loadStats = async () => {
    try {
      const data = await api.getStatsSummary();
      setStats(data);
    } catch (err) {
      setError('Failed to load stats');
    }
  };

  const loadSessions = async () => {
    try {
      const data = await api.listSessions();
      setSessions(data);
    } catch (err) {
      setError('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    loadSessions();
  }, []);

  const handleCreated = () => {
    setShowCreate(false);
    loadSessions();
    loadStats();
  };

  if (loading) return <div className="loading">Loading dashboard…</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Atlas Workbench</h1>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary">
          New Session
        </button>
      </header>

      {stats && (
        <section className="stats-section">
          <h2>Savings Summary</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-value">{stats.tokens_before.toLocaleString()}</span>
              <span className="stat-label">Tokens Before</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.tokens_saved.toLocaleString()}</span>
              <span className="stat-label">Tokens Saved</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{(stats.overall_savings_ratio * 100).toFixed(1)}%</span>
              <span className="stat-label">Savings Ratio</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.total_sessions}</span>
              <span className="stat-label">Total Sessions</span>
            </div>
          </div>
        </section>
      )}

      {sessions && <SessionList sessions={sessions} />}

      {showCreate && (
        <CreateSessionForm
          onClose={() => setShowCreate(false)}
          onSuccess={handleCreated}
        />
      )}
    </div>
  );
}