import type { CompressionSession, PaginatedResponse } from '../types';

interface SessionListProps {
  sessions: PaginatedResponse<CompressionSession>;
}

export function SessionList({ sessions }: SessionListProps) {
  if (!sessions.items.length) {
    return (
      <section className="sessions-section">
        <h2>Sessions</h2>
        <p className="empty-state">No sessions yet. Create one to begin.</p>
      </section>
    );
  }

  return (
    <section className="sessions-section">
      <h2>Sessions</h2>
      <table className="sessions-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Mode</th>
            <th>Provider</th>
            <th>Tokens Saved</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {sessions.items.map((s) => (
            <tr key={s.id}>
              <td>{s.session_name}</td>
              <td>{s.mode}</td>
              <td>{s.provider}</td>
              <td>{s.tokens_saved.toLocaleString()}</td>
              <td>{new Date(s.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <span>Page {sessions.page} of {sessions.total_pages}</span>
      </div>
    </section>
  );
}