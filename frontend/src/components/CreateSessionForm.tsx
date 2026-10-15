import { useState } from 'react';
import { api } from '../api/client';

interface CreateSessionFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function CreateSessionForm({ onClose, onSuccess }: CreateSessionFormProps) {
  const [sessionName, setSessionName] = useState('');
  const [mode, setMode] = useState<'compress' | 'summarize' | 'off'>('compress');
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-4');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createSession({ session_name: sessionName, mode, provider, model });
      onSuccess();
    } catch (err) {
      setError('Failed to create session');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h2>New Compression Session</h2>
        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <label>Session Name</label>
            <input
              type="text"
              value={sessionName}
              onChange={(e) => setSessionName(e.target.value)}
              required
              minLength={1}
              maxLength={255}
            />
          </div>
          <div className="form-group">
            <label>Mode</label>
            <select value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
              <option value="compress">Compress</option>
              <option value="summarize">Summarize</option>
              <option value="off">Off</option>
            </select>
          </div>
          <div className="form-group">
            <label>Provider</label>
            <input
              type="text"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Model</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              required
            />
          </div>
          {error && <div className="error">{error}</div>}
          <div className="form-actions">
            <button type="button" onClick={onClose} disabled={submitting}>Cancel</button>
            <button type="submit" disabled={submitting || !sessionName}>
              {submitting ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}