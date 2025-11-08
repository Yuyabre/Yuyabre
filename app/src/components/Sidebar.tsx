import { useState, ChangeEvent } from 'react';
import { useStore } from '../store/useStore';
import type { ViewId } from '../types';
import './Sidebar.css';

interface SidebarItemProps {
  icon: string;
  label: string;
  active: boolean;
  onClick: () => void;
}

function SidebarItem({ icon, label, active, onClick }: SidebarItemProps) {
  const { sidebarCollapsed } = useStore();
  
  return (
    <button
      className={`sidebar-item ${active ? 'active' : ''}`}
      onClick={onClick}
      title={sidebarCollapsed ? label : undefined}
    >
      <span className="sidebar-icon">{icon}</span>
      {!sidebarCollapsed && <span className="sidebar-label">{label}</span>}
    </button>
  );
}

interface SidebarSwitchProps {
  label: string;
  checked: boolean;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  disabled: boolean;
}

function SidebarSwitch({ label, checked, onChange, disabled }: SidebarSwitchProps) {
  const { sidebarCollapsed } = useStore();
  
  return (
    <div className="sidebar-switch">
      {!sidebarCollapsed && <label className="switch-label">{label}</label>}
      <div className="switch-wrapper">
        <input
          type="checkbox"
          className="switch-input"
          checked={checked}
          onChange={onChange}
          disabled={disabled}
        />
        <span className="switch-slider"></span>
      </div>
    </div>
  );
}

interface View {
  id: ViewId;
  label: string;
  icon: string;
}

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, activeView, setActiveView } = useStore();
  
  const views: View[] = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'inventory', label: 'Inventory', icon: '📦' },
    { id: 'orders', label: 'Orders', icon: '🛒' },
    { id: 'expenses', label: 'Expenses', icon: '💰' },
  ];

  // Placeholder switchers (non-functional)
  const [autoOrder, setAutoOrder] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [lowStockAlerts, setLowStockAlerts] = useState(true);

  return (
    <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        {!sidebarCollapsed && (
          <div className="sidebar-title">
            <h2>Yuyabre</h2>
          </div>
        )}
        <button
          className="sidebar-toggle"
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          )}
        </button>
      </div>

      <nav className="sidebar-nav">
        {views.map(view => (
          <SidebarItem
            key={view.id}
            icon={view.icon}
            label={view.label}
            active={activeView === view.id}
            onClick={() => setActiveView(view.id)}
          />
        ))}
      </nav>

      {!sidebarCollapsed && (
        <div className="sidebar-settings">
          <div className="settings-section">
            <h3 className="settings-title">Settings</h3>
            <SidebarSwitch
              label="Auto Order"
              checked={autoOrder}
              onChange={(e) => setAutoOrder(e.target.checked)}
              disabled={true}
            />
            <SidebarSwitch
              label="Notifications"
              checked={notifications}
              onChange={(e) => setNotifications(e.target.checked)}
              disabled={true}
            />
            <SidebarSwitch
              label="Low Stock Alerts"
              checked={lowStockAlerts}
              onChange={(e) => setLowStockAlerts(e.target.checked)}
              disabled={true}
            />
          </div>
        </div>
      )}

      {sidebarCollapsed && (
        <div className="sidebar-settings-collapsed">
          <button className="sidebar-icon-button" title="Settings">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"></path>
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}

