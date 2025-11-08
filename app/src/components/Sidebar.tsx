import { useState, useEffect } from "react";
import { useStore } from "../store/useStore";
import {
  IconChevronLeft,
  IconChevronRight,
  IconPackage,
  IconShoppingCart,
  IconCurrencyEuro,
  IconUsers,
  IconSettings,
} from "@tabler/icons-react";
import { userApi } from "../lib/api";
import { InventoryModal } from "./modals/InventoryModal";
import { OrdersModal } from "./modals/OrdersModal";
import { ExpensesModal } from "./modals/ExpensesModal";
import { GroupModal } from "./modals/GroupModal";
import packageJson from "../../package.json";
import "./Sidebar.css";

interface SidebarButtonProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}

function SidebarButton({ icon, label, onClick }: SidebarButtonProps) {
  const { sidebarCollapsed } = useStore();

  return (
    <button
      className="sidebar-item"
      onClick={onClick}
      title={sidebarCollapsed ? label : undefined}
    >
      <span className="sidebar-icon">{icon}</span>
      {!sidebarCollapsed && <span className="sidebar-label">{label}</span>}
    </button>
  );
}

export default function Sidebar() {
  const {
    sidebarCollapsed,
    toggleSidebar,
    currentUser,
    currentGroup,
    setCurrentUser,
    setCurrentGroup,
  } = useStore();

  const [inventoryOpen, setInventoryOpen] = useState(false);
  const [ordersOpen, setOrdersOpen] = useState(false);
  const [expensesOpen, setExpensesOpen] = useState(false);
  const [groupOpen, setGroupOpen] = useState(false);

  useEffect(() => {
    // Load user session on mount
    userApi.getSession().then((session) => {
      setCurrentUser(session.user);
      setCurrentGroup(session.group);
    });
  }, [setCurrentUser, setCurrentGroup]);

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
      {/* User Section as Header */}
      <div className="sidebar-user-section sidebar-header">
        {sidebarCollapsed ? (
          <button
            className="sidebar-toggle"
            onClick={toggleSidebar}
            aria-label="Expand sidebar"
          >
            <IconChevronRight className="size-5" />
          </button>
        ) : (
          <>
            {currentUser ? (
              <>
                <div className="sidebar-user-info">
                  <div className="sidebar-user-avatar">
                    {currentUser.avatar ? (
                      <img src={currentUser.avatar} alt={currentUser.name} />
                    ) : (
                      <span>{getInitials(currentUser.name)}</span>
                    )}
                  </div>
                  <div className="sidebar-user-details">
                    <div className="sidebar-user-name">{currentUser.name}</div>
                    <div className="sidebar-user-email">
                      {currentUser.email}
                    </div>
                  </div>
                </div>
                <button
                  className="sidebar-toggle sidebar-toggle-user"
                  onClick={toggleSidebar}
                  aria-label="Collapse sidebar"
                >
                  <IconChevronLeft className="size-5" />
                </button>
              </>
            ) : (
              <>
                <div className="sidebar-user-info">
                  <div className="sidebar-user-avatar">
                    <span>?</span>
                  </div>
                  <div className="sidebar-user-details">
                    <div className="sidebar-user-name">Loading...</div>
                    <div className="sidebar-user-email">Please wait</div>
                  </div>
                </div>
                <button
                  className="sidebar-toggle sidebar-toggle-user"
                  onClick={toggleSidebar}
                  aria-label="Collapse sidebar"
                >
                  <IconChevronLeft className="size-5" />
                </button>
              </>
            )}
          </>
        )}
      </div>

      {/* Group Section */}
      {currentGroup && !sidebarCollapsed && (
        <div className="sidebar-group-section">
          <button
            onClick={() => setGroupOpen(true)}
            className="sidebar-group-header-button"
          >
            <IconUsers className="size-4" />
            <span className="sidebar-group-name">{currentGroup.name}</span>
          </button>
        </div>
      )}

      <nav className="sidebar-nav">
        <SidebarButton
          icon={<IconPackage className="size-5" />}
          label="Inventory"
          onClick={() => setInventoryOpen(true)}
        />
        <SidebarButton
          icon={<IconShoppingCart className="size-5" />}
          label="Orders"
          onClick={() => setOrdersOpen(true)}
        />
        <SidebarButton
          icon={<IconCurrencyEuro className="size-5" />}
          label="Expenses"
          onClick={() => setExpensesOpen(true)}
        />
      </nav>

      {!sidebarCollapsed && (
        <div className="sidebar-settings">
          <button className="sidebar-settings-button">
            <IconSettings className="size-4" />
            <span>Settings</span>
          </button>
        </div>
      )}

      {sidebarCollapsed && (
        <div className="sidebar-settings-collapsed">
          <button className="sidebar-icon-button" title="Settings">
            <IconSettings className="size-5" />
          </button>
        </div>
      )}

      {/* Footer */}
      {!sidebarCollapsed && (
        <div className="sidebar-footer">
          <div className="sidebar-footer-title">
            Yuyabre v{packageJson.version}
          </div>
        </div>
      )}

      {/* Modals */}
      <InventoryModal open={inventoryOpen} onOpenChange={setInventoryOpen} />
      <OrdersModal open={ordersOpen} onOpenChange={setOrdersOpen} />
      <ExpensesModal open={expensesOpen} onOpenChange={setExpensesOpen} />
      <GroupModal open={groupOpen} onOpenChange={setGroupOpen} />
    </div>
  );
}
