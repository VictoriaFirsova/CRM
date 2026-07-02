import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  FileText,
  FileSpreadsheet,
  FileCheck,
  FolderOpen,
  LogOut,
  Moon,
  Sun,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const nav = [
  { to: '/', label: 'Дашборд', icon: LayoutDashboard },
  { to: '/clients', label: 'Клиенты', icon: Users },
  { to: '/contracts', label: 'Договоры', icon: FileText },
  { to: '/invoices', label: 'Счета', icon: FileSpreadsheet },
  { to: '/acts', label: 'Акты', icon: FileCheck },
  { to: '/documents', label: 'Документы', icon: FolderOpen },
]

const pageTitles: Record<string, string> = {
  '/': 'Дашборд',
  '/clients': 'Клиенты',
  '/contracts': 'Договоры',
  '/invoices': 'Счета',
  '/acts': 'Акты',
  '/documents': 'Документы',
}

export default function Layout() {
  const { user, logout } = useAuth()
  const { theme, toggle } = useTheme()
  const location = useLocation()

  const basePath = '/' + (location.pathname.split('/')[1] || '')
  const sectionTitle = pageTitles[basePath] || 'CRM'

  return (
    <div className="flex min-h-screen bg-surface">
      {/* Icon sidebar — как в референсе */}
      <aside className="flex w-[72px] shrink-0 flex-col items-center border-r border-surface-border bg-surface-sidebar py-5">
        <div
          className="mb-6 flex h-11 w-11 items-center justify-center rounded-full bg-primary text-lg font-bold text-white shadow-md"
          title="CRM"
        >
          C
        </div>

        <nav className="flex flex-1 flex-col items-center gap-1">
          {nav.map(({ to, label, icon: Icon }, i) => (
            <div key={to} className="flex flex-col items-center">
              {i > 0 && i === 1 && <div className="sidebar-divider w-8" />}
              <NavLink
                to={to}
                end={to === '/'}
                title={label}
                className={({ isActive }) => `nav-icon-btn ${isActive ? 'active' : ''}`}
              >
                <Icon size={20} strokeWidth={1.75} />
              </NavLink>
            </div>
          ))}
        </nav>

        <div className="sidebar-divider w-8" />
        <button type="button" onClick={toggle} className="nav-icon-btn mb-1" title="Тема">
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
        <button type="button" onClick={logout} className="nav-icon-btn" title="Выход">
          <LogOut size={18} />
        </button>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar */}
        <div className="flex items-center justify-between border-b border-surface-border/80 bg-surface-sidebar/50 px-6 py-3 backdrop-blur-sm">
          <span className="text-sm font-medium text-foreground-muted">{sectionTitle}</span>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-foreground">{user?.full_name}</p>
              <p className="text-[11px] uppercase tracking-wide text-foreground-faint">{user?.role}</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-light text-sm font-semibold text-primary">
              {user?.full_name?.charAt(0) ?? '?'}
            </div>
          </div>
        </div>

        <main className="flex-1 overflow-auto p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
