import { useState, useEffect, type FormEvent } from 'react'
import axios from 'axios'
import { useLottie } from 'lottie-react'
import { API_ENDPOINTS } from './config'
import loginAnimation from './assets/login_lottie.json'
import './Login.css'

interface LoginProps {
  onLogin: (token: string, userId: number) => void
}

function Login({ onLogin }: LoginProps) {
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [isCredentialLoading, setIsCredentialLoading] = useState(false)
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const [error, setError] = useState('')
  const { View: loginAnimationView } = useLottie({
    animationData: loginAnimation,
    loop: true,
    autoplay: true,
  })

  useEffect(() => {
    // Check for OAuth callback parameters
    const urlParams = new URLSearchParams(window.location.search)
    const token = urlParams.get('token')
    const userId = urlParams.get('user_id')

    if (token && userId) {
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
      onLogin(token, parseInt(userId))
    }
  }, [onLogin])

  const handleGoogleLogin = async () => {
    setIsGoogleLoading(true)
    setError('')

    try {
      const response = await axios.get(API_ENDPOINTS.AUTH.GOOGLE_LOGIN)
      window.location.href = response.data.auth_url
    } catch (err) {
      setError('Failed to initiate Google login. Please try again.')
      setIsGoogleLoading(false)
    }
  }

  const handleCredentialLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsCredentialLoading(true)
    setError('')

    try {
      const response = await axios.post(API_ENDPOINTS.AUTH.LOGIN, {
        identifier,
        password,
      })
      onLogin(response.data.access_token, response.data.user.id)
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
      } else {
        setError('Login failed. Please check your credentials.')
      }
    } finally {
      setIsCredentialLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-header-top">
            <h1>Split smart. Settle fast.</h1>
            <p>Slice keeps group expenses crisp, visible, and less awkward to manage.</p>
          </div>

          <div className="login-lottie-shell" aria-hidden="true">
            <div className="login-lottie">{loginAnimationView}</div>
          </div>
        </div>

        <div className="login-content">
          <div className="login-form-wrap">
            <p className="login-description">
              Sign in to your expense workspace and keep every shared payment trail in one clean view.
            </p>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <form className="login-form" onSubmit={handleCredentialLogin}>
              <div className="form-field">
                <label htmlFor="identifier">Username or email</label>
                <input
                  id="identifier"
                  type="text"
                  value={identifier}
                  onChange={(event) => setIdentifier(event.target.value)}
                  placeholder="Enter username or email"
                  autoComplete="username"
                  disabled={isCredentialLoading || isGoogleLoading}
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter password"
                  autoComplete="current-password"
                  disabled={isCredentialLoading || isGoogleLoading}
                  required
                />
              </div>

              <button
                className="credential-login-btn"
                type="submit"
                disabled={isCredentialLoading || isGoogleLoading}
              >
                {isCredentialLoading ? <div className="loading-spinner"></div> : 'Sign in'}
              </button>
            </form>

            <div className="login-divider">
              <span>or</span>
            </div>

            <button
              className="google-login-btn"
              onClick={handleGoogleLogin}
              disabled={isCredentialLoading || isGoogleLoading}
            >
              {isGoogleLoading ? (
                <div className="loading-spinner"></div>
              ) : (
                <>
                  <svg className="google-icon" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </>
              )}
            </button>
          </div>
        </div>

        <div className="login-footer">
          <p>By continuing, you agree to our Terms of Service and Privacy Policy</p>
        </div>
      </div>
    </div>
  )
}

export default Login
