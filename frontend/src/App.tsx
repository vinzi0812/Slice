import { useEffect, useState } from 'react'
import axios from 'axios'
import { API_ENDPOINTS } from './config'
import Login from './Login'
import './App.css'

interface User {
  id: number
  name: string
  username: string
  profile_picture?: string | null
}

interface GroupSummary {
  id: number
  name: string
  description: string | null
  simplified_debts: boolean
  created_by: number
  created_at: string
  member_count: number
}

interface GroupMember {
  id: number
  name: string
  email: string
  username?: string | null
}

interface Expense {
  id: number
  group_id: number
  description: string
  amount: number
  expense_type: string
  expense_date: string
  created_at: string
  paid_by: Array<{ id: number; user_id: number; amount_paid: number }>
  split_by: Array<{
    id: number
    user_id: number
    amount_owed: number
    split_type: string
    split_value: number | null
  }>
}

interface GroupDetail extends GroupSummary {
  members: GroupMember[]
}

type ActiveView =
  | { type: 'home' }
  | { type: 'group'; groupId: number }
  | { type: 'create-group' }

function HomeIcon() {
  return (
    <svg className="sidebar-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M3 10.5 12 3l9 7.5v9a1.5 1.5 0 0 1-1.5 1.5h-4.5V14h-6v7H4.5A1.5 1.5 0 0 1 3 19.5z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function PlusGroupIcon() {
  return (
    <svg className="sidebar-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm0 0c-3.314 0-6 1.79-6 4v1h8.5M17 8v8M13 12h8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function LogoutIcon() {
  return (
    <svg className="sidebar-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M10 5H6.5A1.5 1.5 0 0 0 5 6.5v11A1.5 1.5 0 0 0 6.5 19H10M14 16l4-4-4-4M18 12H9"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [groups, setGroups] = useState<GroupSummary[]>([])
  const [selectedGroup, setSelectedGroup] = useState<GroupDetail | null>(null)
  const [activeView, setActiveView] = useState<ActiveView>({ type: 'home' })
  const [groupsExpanded, setGroupsExpanded] = useState(true)
  const [isLoadingGroup, setIsLoadingGroup] = useState(false)
  const [groupError, setGroupError] = useState('')
  const [groupName, setGroupName] = useState('')
  const [groupDescription, setGroupDescription] = useState('')
  const [selectedMemberIds, setSelectedMemberIds] = useState<number[]>([])
  const [isCreatingGroup, setIsCreatingGroup] = useState(false)
  const [profileImageFailed, setProfileImageFailed] = useState(false)
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [memberBalances, setMemberBalances] = useState<Map<number, number>>(new Map())
  const [isLoadingExpenses, setIsLoadingExpenses] = useState(false)
  const [expandedExpenseId, setExpandedExpenseId] = useState<number | null>(null)

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    const storedUserId = localStorage.getItem('user_id')

    if (storedToken && storedUserId) {
      setToken(storedToken)
      void fetchUserInfo(storedToken)
    }
  }, [])

  useEffect(() => {
    if (!token || !user) {
      return
    }

    void Promise.all([fetchUsers(token), fetchGroups(token)])
  }, [token, user])

  useEffect(() => {
    setProfileImageFailed(false)
  }, [user?.id, user?.profile_picture])

  useEffect(() => {
    if (activeView.type !== 'group' || !token) {
      return
    }

    void fetchGroupDetail(activeView.groupId, token)
  }, [activeView, token])

  const fetchUserInfo = async (authToken: string) => {
    try {
      const response = await axios.get(API_ENDPOINTS.AUTH.ME, {
        headers: { Authorization: `Bearer ${authToken}` },
      })
      setUser(response.data)
    } catch (error) {
      console.error('Error fetching user info:', error)
      handleLogout()
    }
  }

  const fetchUsers = async (authToken: string) => {
    try {
      const response = await axios.get(API_ENDPOINTS.USERS.LIST, {
        headers: { Authorization: `Bearer ${authToken}` },
      })
      setUsers(response.data)
    } catch (error) {
      console.error('Error fetching users:', error)
    }
  }

  const fetchGroups = async (authToken: string) => {
    try {
      const response = await axios.get(API_ENDPOINTS.GROUPS.LIST, {
        headers: { Authorization: `Bearer ${authToken}` },
      })
      setGroups(response.data)
    } catch (error) {
      console.error('Error fetching groups:', error)
    }
  }

  const fetchGroupDetail = async (groupId: number, authToken: string) => {
    setIsLoadingGroup(true)
    setGroupError('')

    try {
      const response = await axios.get(API_ENDPOINTS.GROUPS.GET(groupId), {
        headers: { Authorization: `Bearer ${authToken}` },
      })
      setSelectedGroup(response.data)
      // Fetch expenses and member balances when group is loaded
      void fetchGroupExpenses(groupId, authToken)
    } catch (error) {
      console.error('Error fetching group details:', error)
      setSelectedGroup(null)
      setGroupError('Failed to load group details.')
    } finally {
      setIsLoadingGroup(false)
    }
  }

  const fetchGroupExpenses = async (groupId: number, authToken: string) => {
    setIsLoadingExpenses(true)
    try {
      const response = await axios.get(API_ENDPOINTS.EXPENSES.GROUP(groupId), {
        headers: { Authorization: `Bearer ${authToken}` },
      })
      setExpenses(response.data)

      // Build member balances map from expenses
      const balances = new Map<number, number>()
      response.data.forEach((expense: Expense) => {
        expense.paid_by.forEach((contributor) => {
          balances.set(contributor.user_id, (balances.get(contributor.user_id) || 0) + contributor.amount_paid)
        })
        expense.split_by.forEach((split) => {
          balances.set(split.user_id, (balances.get(split.user_id) || 0) - split.amount_owed)
        })
      })
      setMemberBalances(balances)
    } catch (error) {
      console.error('Error fetching expenses:', error)
    } finally {
      setIsLoadingExpenses(false)
    }
  }

  const handleLogin = (authToken: string, userId: number) => {
    setToken(authToken)
    localStorage.setItem('auth_token', authToken)
    localStorage.setItem('user_id', userId.toString())
    void fetchUserInfo(authToken)
  }

  const handleLogout = () => {
    const authToken = token
    if (authToken) {
      void axios.post(
        API_ENDPOINTS.AUTH.LOGOUT,
        {},
        {
          headers: { Authorization: `Bearer ${authToken}` },
        },
      ).catch((error) => {
        console.error('Error logging out:', error)
      })
    }

    setUser(null)
    setToken(null)
    setGroups([])
    setUsers([])
    setSelectedGroup(null)
    setActiveView({ type: 'home' })
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_id')
  }

  const handleCreateGroup = async () => {
    if (!token || !groupName.trim()) {
      return
    }

    setIsCreatingGroup(true)
    setGroupError('')

    try {
      const response = await axios.post(
        API_ENDPOINTS.GROUPS.CREATE,
        {
          name: groupName.trim(),
          description: groupDescription.trim() || null,
          member_ids: selectedMemberIds,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      )

      setGroupName('')
      setGroupDescription('')
      setSelectedMemberIds([])
      await fetchGroups(token)
      setGroupsExpanded(true)
      setSelectedGroup(response.data)
      setActiveView({ type: 'group', groupId: response.data.id })
    } catch (error) {
      console.error('Error creating group:', error)
      if (axios.isAxiosError(error)) {
        setGroupError(error.response?.data?.detail || 'Failed to create group.')
      } else {
        setGroupError('Failed to create group.')
      }
    } finally {
      setIsCreatingGroup(false)
    }
  }

  const toggleMemberSelection = (memberId: number) => {
    setSelectedMemberIds((currentIds) =>
      currentIds.includes(memberId)
        ? currentIds.filter((id) => id !== memberId)
        : [...currentIds, memberId],
    )
  }

  const openHome = () => {
    setActiveView({ type: 'home' })
    setGroupError('')
  }

  const openCreateGroup = () => {
    setActiveView({ type: 'create-group' })
    setGroupError('')
  }

  const openGroup = (groupId: number) => {
    setActiveView({ type: 'group', groupId })
    setGroupError('')
  }

  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  const firstName = user.name.split(' ')[0] || user.name
  const userInitial = user.name.charAt(0).toUpperCase()
  const selectedGroupSummary =
    activeView.type === 'group' ? groups.find((group) => group.id === activeView.groupId) : null
  const homeGroupPreview = groups.slice(0, 3)

  return (
    <div className="App">
      <div className="app-shell">
        <aside className="app-sidebar">
          <div className="sidebar-top">

            <div className="user-badge">
              <div className="user-badge-avatar-wrap">
                {user.profile_picture && !profileImageFailed ? (
                  <img
                    className="user-badge-avatar"
                    src={user.profile_picture}
                    alt={user.name}
                    referrerPolicy="no-referrer"
                    onError={() => setProfileImageFailed(true)}
                  />
                ) : (
                  <div className="user-badge-avatar user-badge-avatar-fallback">{userInitial}</div>
                )}
              </div>
              <div className="user-badge-content">
                <div className="user-badge-label">Signed in as</div>
                <div className="user-badge-name">{user.name}</div>
                <div className="user-badge-email">{user.username}</div>
              </div>
            </div>

            <nav className="sidebar-nav" aria-label="Sidebar">
              <button
                className={`sidebar-link ${activeView.type === 'home' ? 'is-active' : ''}`}
                onClick={openHome}
              >
                <span className="sidebar-link-main">
                  <HomeIcon />
                  <span>Home</span>
                </span>
              </button>

              <div className="sidebar-group">
                <button
                  className={`sidebar-link sidebar-link-split ${activeView.type === 'group' ? 'is-active' : ''}`}
                  onClick={() => setGroupsExpanded((value) => !value)}
                >
                  <span>Groups</span>
                  <span className={`sidebar-caret ${groupsExpanded ? 'is-open' : ''}`}>▾</span>
                </button>

                {groupsExpanded && (
                  <div className="sidebar-submenu">
                    {groups.length === 0 ? (
                      <div className="sidebar-empty">No groups yet</div>
                    ) : (
                      groups.map((group) => (
                        <button
                          key={group.id}
                          className={`sidebar-submenu-item ${
                            activeView.type === 'group' && activeView.groupId === group.id ? 'is-active' : ''
                          }`}
                          onClick={() => openGroup(group.id)}
                        >
                          {group.name}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>

              <button
                className={`sidebar-link ${activeView.type === 'create-group' ? 'is-active' : ''}`}
                onClick={openCreateGroup}
              >
                <span className="sidebar-link-main">
                  <PlusGroupIcon />
                  <span>Create Group</span>
                </span>
              </button>
            </nav>
          </div>

          <div className="sidebar-bottom">
            <button className="logout-btn" onClick={handleLogout}>
              <span className="sidebar-link-main">
                <LogoutIcon />
                <span>Logout</span>
              </span>
            </button>
          </div>
        </aside>

        <main className="app-main">
          {activeView.type === 'home' && (
            <>
              <section className="dashboard-hero">
                <div>
                  <span className="panel-kicker">Home</span>
                  <h2 className="welcome-title">Welcome back, {firstName}.</h2>
                  <p className="welcome-copy">
                    Your main workspace surfaces the people you can add, the groups you belong to, and a quick path into the next shared expense flow.
                  </p>

                  <div className="hero-stat-grid">
                    <div className="hero-stat-card">
                      <div className="stat-label">Your groups</div>
                      <div className="stat-value">{groups.length}</div>
                    </div>
                    <div className="hero-stat-card">
                      <div className="stat-label">Visible users</div>
                      <div className="stat-value">{users.length}</div>
                    </div>
                    <div className="hero-stat-card">
                      <div className="stat-label">Active identity</div>
                      <div className="stat-value">1</div>
                    </div>
                  </div>
                </div>

                <div className="hero-aside">
                  <span className="hero-chip">Navigation ready</span>
                  <h3>Groups now live in the sidebar</h3>
                  <p>
                    Expand the groups menu to jump directly into a shared space, or create a new one from the next action.
                  </p>
                </div>
              </section>

              <section className="dashboard-grid">
                <div className="panel">
                  <div className="panel-header">
                    <div>
                      <span className="panel-kicker">Groups</span>
                      <h3 className="panel-title">Your current circles</h3>
                      <p className="panel-copy">
                        These are the groups where you are already a member.
                      </p>
                    </div>
                    <button className="panel-action" onClick={() => token && void fetchGroups(token)}>Refresh</button>
                  </div>

                  <div className="user-list">
                    {homeGroupPreview.length === 0 ? (
                      <div className="empty-state">No groups found yet. Use Create Group to start one.</div>
                    ) : (
                      homeGroupPreview.map((group) => (
                        <button className="user-card user-card-button" key={group.id} onClick={() => openGroup(group.id)}>
                          <div>
                            <div className="user-card-name">{group.name}</div>
                            <div className="user-card-email">
                              {group.member_count} member{group.member_count === 1 ? '' : 's'}
                            </div>
                          </div>
                          <div className="user-avatar">{group.name.charAt(0).toUpperCase()}</div>
                        </button>
                      ))
                    )}
                  </div>
                </div>

                <div className="panel">
                  <div>
                    <span className="panel-kicker">People</span>
                    <h3 className="section-title">Available members</h3>
                    <p className="form-copy">
                      Pick from these users when creating a new group.
                    </p>
                  </div>

                  <div className="member-pill-grid">
                    {users.map((listedUser) => (
                      <div className="member-pill" key={listedUser.id}>
                        <span className="member-pill-avatar">{listedUser.name.charAt(0).toUpperCase()}</span>
                        <div>
                          <div className="member-pill-name">{listedUser.name}</div>
                          <div className="member-pill-email">{listedUser.username}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            </>
          )}

          {activeView.type === 'group' && (
            <div className="group-view-container">
              {isLoadingGroup ? (
                <div className="empty-state">Loading group details...</div>
              ) : groupError ? (
                <div className="empty-state">{groupError}</div>
              ) : selectedGroup ? (
                <>
                  <main className="group-main-content">
                    {/* Group Title Bar */}
                    <div className="group-title-bar">
                      <div className="group-avatar">{selectedGroupSummary?.name.charAt(0).toUpperCase()}</div>
                      <div className="group-info">
                        <h1 className="group-name">{selectedGroupSummary?.name}</h1>
                        <p className="group-description">
                          {selectedGroup.description || 'No description'}
                        </p>
                      </div>
                    </div>

                    {/* User Balance */}
                    <div className="user-balance-card">
                        <div className="balance-display">
                          <div className="balance-label">Your Balance</div>
                          <div
                            className={`balance-amount ${
                              memberBalances.get(user?.id || 0) && memberBalances.get(user?.id || 0)! > 0
                                ? 'balance-positive'
                                : 'balance-negative'
                            }`}
                          >
                            {memberBalances.get(user?.id || 0)
                              ? (memberBalances.get(user?.id || 0)! > 0 ? '+' : '') +
                                memberBalances.get(user?.id || 0)!.toFixed(2)
                              : '0.00'}
                          </div>
                        </div>

                        <div className="balance-details">
                          {memberBalances.get(user?.id || 0) && memberBalances.get(user?.id || 0)! !== 0 ? (
                            <>
                              {(() => {
                                // Calculate who owes the user and who the user owes
                                const userBalance = memberBalances.get(user?.id || 0) || 0
                                const owedByMembers: Array<{ name: string; amount: number }> = []
                                const owesMembers: Array<{ name: string; amount: number }> = []

                                selectedGroup.members
                                  .filter((m) => m.id !== user?.id)
                                  .forEach((member) => {
                                    const memberBalance = memberBalances.get(member.id) || 0

                                    // In non-simplified mode, we can have both owed and owing
                                    // If member balance is negative, they owe the user
                                    if (memberBalance < 0) {
                                      owedByMembers.push({ name: member.name, amount: Math.abs(memberBalance) })
                                    }
                                    // If member balance is positive, the user owes them
                                    if (memberBalance > 0) {
                                      owesMembers.push({ name: member.name, amount: memberBalance })
                                    }
                                  })

                                const hasBothOwedAndOwes = owedByMembers.length > 0 && owesMembers.length > 0

                                return (
                                  <div className={`balance-details-content ${hasBothOwedAndOwes ? 'split-view' : 'single-view'}`}>
                                    {hasBothOwedAndOwes ? (
                                      <>
                                        <div className="balance-column owes-column">
                                          <div className="column-header">You owe</div>
                                          <div className="owed-to-list">
                                            {owesMembers.map((item) => (
                                              <div key={item.name} className="owed-item owes-item">
                                                <span className="member-name-short">{item.name}</span>
                                                <span className="owed-amount owes-amount">${item.amount.toFixed(2)}</span>
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                        <div className="balance-column-divider"></div>
                                        <div className="balance-column owed-column">
                                          <div className="column-header">You're owed</div>
                                          <div className="owed-to-list">
                                            {owedByMembers.map((item) => (
                                              <div key={item.name} className="owed-item owed-item-positive">
                                                <span className="member-name-short">{item.name}</span>
                                                <span className="owed-amount owed-amount-positive">${item.amount.toFixed(2)}</span>
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      </>
                                    ) : (
                                      <>
                                        <div className="balance-hint">
                                          {userBalance > 0 ? "You're owed" : 'You owe'}
                                        </div>
                                        <div className="owed-to-list">
                                          {(userBalance > 0 ? owedByMembers : owesMembers).map((item) => (
                                            <div key={item.name} className="owed-item">
                                              <span className="member-name-short">{item.name}</span>
                                              <span className={`owed-amount ${userBalance > 0 ? 'owed-amount-positive' : ''}`}>
                                                ${item.amount.toFixed(2)}
                                              </span>
                                            </div>
                                          ))}
                                        </div>
                                      </>
                                    )}
                                  </div>
                                )
                              })()}
                            </>
                          ) : (
                            <div className="balance-settled">All settled!</div>
                          )}
                        </div>
                      </div>

                    {/* Expenses List */}
                    <div className="expenses-section">
                      <h2 className="section-title">Expenses</h2>
                      {isLoadingExpenses ? (
                        <div className="empty-state">Loading expenses...</div>
                      ) : expenses.length === 0 ? (
                        <div className="empty-state">No expenses in this group yet.</div>
                      ) : (
                        <div className="expenses-list">
                          {expenses.map((expense) => {
                            // Calculate what the current user paid for this expense
                            const userPaidEntry = expense.paid_by.find(p => p.user_id === user?.id)
                            const userPaid = userPaidEntry ? userPaidEntry.amount_paid : 0

                            // Calculate what the current user owes for this expense
                            const userSplit = expense.split_by.find(s => s.user_id === user?.id)
                            const userOwes = userSplit ? userSplit.amount_owed : 0

                            // Get payer names
                            const payerNames = expense.paid_by.map(p => {
                              const payer = selectedGroup.members.find(m => m.id === p.user_id)
                              return payer ? payer.name : 'Unknown'
                            })

                            const payerText = payerNames.length === 1
                              ? `${payerNames[0]} paid ${expense.amount.toFixed(2)}`
                              : `${payerNames.length} people paid ${expense.amount.toFixed(2)}`

                            // Format date
                            const date = new Date(expense.expense_date)
                            const day = date.getDate()
                            const month = date.toLocaleString('default', { month: 'short' })

                            // Determine the amount to display and label
                            let displayAmount = 0
                            let displayLabel = ''
                            let amountClass = 'amount-settled'

                            if (userPaid > 0) {
                              // User paid for this expense - show how much extra they lent
                              displayAmount = userPaid - userOwes
                              displayLabel = 'You lent'
                              amountClass = displayAmount > 0 ? 'amount-lent' : 'amount-settled'
                            } else if (userOwes > 0) {
                              // User didn't pay but owes money - show how much they owe
                              displayAmount = userOwes
                              displayLabel = 'You owe'
                              amountClass = 'amount-owed'
                            } else {
                              // User didn't pay and doesn't owe - settled
                              displayAmount = 0
                              displayLabel = 'Settled'
                              amountClass = 'amount-settled'
                            }

                            return (
                              <div
                                className={`expense-card ${expandedExpenseId === expense.id ? 'is-expanded' : ''}`}
                                key={expense.id}
                              >
                                <button
                                  className="expense-card-button"
                                  onClick={() =>
                                    setExpandedExpenseId(
                                      expandedExpenseId === expense.id ? null : expense.id,
                                    )
                                  }
                                >
                                  <div className="expense-date">
                                    <div className="expense-day">{day}</div>
                                    <div className="expense-month">{month}</div>
                                  </div>

                                  <div className="expense-type-avatar">
                                    {expense.expense_type.charAt(0).toUpperCase()}
                                  </div>

                                  <div className="expense-content">
                                    <div className="expense-info">
                                      <div className="expense-name">{expense.description}</div>
                                      <div className="expense-payer">{payerText}</div>
                                    </div>
                                  </div>

                                  <div className="expense-amount-section">
                                    <div className={`expense-user-amount ${amountClass}`}>
                                      {displayAmount !== 0 ? (
                                        <>
                                          <div className="amount-label">{displayLabel}</div>
                                          <div className="amount-value">${displayAmount.toFixed(2)}</div>
                                        </>
                                      ) : (
                                        <div className="amount-value">{displayLabel}</div>
                                      )}
                                    </div>
                                  </div>
                                </button>

                                {expandedExpenseId === expense.id && (
                                  <div className="expense-card-details">
                                    <div className="expense-details-grid">
                                      <div className="expense-details-column">
                                        <div className="details-header">Paid by</div>
                                        <div className="details-list">
                                          {expense.paid_by.map((payer) => {
                                            const payerUser = selectedGroup.members.find(
                                              (m) => m.id === payer.user_id,
                                            )
                                            return (
                                              <div key={payer.id} className="detail-item">
                                                <span className="detail-label">
                                                  {payerUser?.name || 'Unknown'}
                                                </span>
                                                <span className="detail-amount paid-amount">
                                                  ${payer.amount_paid.toFixed(2)}
                                                </span>
                                              </div>
                                            )
                                          })}
                                        </div>
                                      </div>

                                      <div className="expense-details-column">
                                        <div className="details-header">Owes</div>
                                        <div className="details-list">
                                          {expense.split_by.map((split) => {
                                            const owesUser = selectedGroup.members.find(
                                              (m) => m.id === split.user_id,
                                            )
                                            return (
                                              <div key={split.id} className="detail-item">
                                                <span className="detail-label">
                                                  {owesUser?.name || 'Unknown'}
                                                </span>
                                                <span className="detail-amount owes-amount">
                                                  ${split.amount_owed.toFixed(2)}
                                                </span>
                                              </div>
                                            )
                                          })}
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  </main>

                  {/* Right Sidebar - Members and Balances */}
                  <aside className="group-sidebar">
                    <div className="sidebar-section">
                      <h2 className="sidebar-title">Members</h2>
                      <div className="members-list">
                        {selectedGroup.members.map((member) => {
                          const balance = memberBalances.get(member.id) || 0
                          return (
                            <div className="member-balance-card" key={member.id}>
                              <div className="member-info">
                                <div className="member-avatar">{member.name.charAt(0).toUpperCase()}</div>
                                <div>
                                  <div className="member-name">{member.name}</div>
                                  <div className="member-email">{member.email}</div>
                                </div>
                              </div>
                              <div
                                className={`member-balance ${balance > 0 ? 'balance-positive' : balance < 0 ? 'balance-negative' : 'balance-zero'}`}
                              >
                                {balance > 0 ? '+' : ''}{balance.toFixed(2)}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </aside>
                </>
              ) : (
                <div className="empty-state">Select a group from the sidebar to view it.</div>
              )}
            </div>
          )}

          {activeView.type === 'create-group' && (
            <section className="panel panel-main">
              <div className="panel-header">
                <div>
                  <span className="panel-kicker">Create</span>
                  <h3 className="panel-title">Create a new group</h3>
                  <p className="panel-copy">
                    Add a name, optional description, and choose members. You are added automatically.
                  </p>
                </div>
              </div>

              {groupError && <div className="empty-state empty-state-error">{groupError}</div>}

              <div className="add-user-form">
                <div className="input-stack">
                  <input
                    type="text"
                    placeholder="Group name"
                    value={groupName}
                    onChange={(event) => setGroupName(event.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Short description"
                    value={groupDescription}
                    onChange={(event) => setGroupDescription(event.target.value)}
                  />
                </div>

                <div className="member-selector">
                  {users
                    .filter((listedUser) => listedUser.id !== user.id)
                    .map((listedUser) => {
                      const isSelected = selectedMemberIds.includes(listedUser.id)
                      return (
                        <button
                          key={listedUser.id}
                          className={`member-select-card ${isSelected ? 'is-selected' : ''}`}
                          onClick={() => toggleMemberSelection(listedUser.id)}
                          type="button"
                        >
                          <span className="member-pill-avatar">{listedUser.name.charAt(0).toUpperCase()}</span>
                          <div>
                            <div className="member-pill-name">{listedUser.name}</div>
                            <div className="member-pill-email">{listedUser.username}</div>
                          </div>
                        </button>
                      )
                    })}
                </div>

                <button className="primary-btn" onClick={handleCreateGroup} disabled={isCreatingGroup}>
                  {isCreatingGroup ? 'Creating group...' : 'Create group'}
                </button>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
