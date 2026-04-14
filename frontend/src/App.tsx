import { useState, useEffect } from 'react'
import axios from 'axios'
import Login from './Login'
import './App.css'

interface User {
  id: number
  name: string
  email: string
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')

  useEffect(() => {
    // Check for stored authentication
    const storedToken = localStorage.getItem('auth_token')
    const storedUserId = localStorage.getItem('user_id')

    if (storedToken && storedUserId) {
      setToken(storedToken)
      fetchUserInfo(storedToken)
    }
  }, [])

  const fetchUserInfo = async (authToken: string) => {
    try {
      const response = await axios.get('http://localhost:8080/auth/me', {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      setUser(response.data)
    } catch (error) {
      console.error('Error fetching user info:', error)
      handleLogout()
    }
  }

  const handleLogin = (authToken: string, userId: number) => {
    setToken(authToken)
    localStorage.setItem('auth_token', authToken)
    localStorage.setItem('user_id', userId.toString())
    fetchUserInfo(authToken)
  }

  const handleLogout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_id')
  }

  const fetchUsers = async () => {
    if (!token) return

    try {
      const response = await axios.get('http://localhost:8080/users/', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setUsers(response.data)
    } catch (error) {
      console.error('Error fetching users:', error)
    }
  }

  const addUser = async () => {
    if (!token) return

    try {
      await axios.post('http://localhost:8080/users/', { name, email }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setName('')
      setEmail('')
      fetchUsers()
    } catch (error) {
      console.error('Error adding user:', error)
    }
  }

  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className="App">
      <header className="app-header">
        <h1>Welcome to Slice, {user.name}!</h1>
        <button className="logout-btn" onClick={handleLogout}>Logout</button>
      </header>

      <div className="app-content">
        <h2>Users</h2>
        <ul>
          {users.map(user => (
            <li key={user.id}>{user.name} - {user.email}</li>
          ))}
        </ul>
        <h2>Add User</h2>
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button onClick={addUser}>Add User</button>
      </div>
    </div>
  )
}

export default App
