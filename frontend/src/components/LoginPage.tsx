import { api } from '../api/client';

export function LoginPage() {
  const handleLogin = () => {
    window.location.href = api.getLoginUrl();
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Atlas Workbench</h1>
        <p>Token compression proxy for AI coding agents.</p>
        <button onClick={handleLogin} className="login-button">
          Sign in with SSO
        </button>
      </div>
    </div>
  );
}