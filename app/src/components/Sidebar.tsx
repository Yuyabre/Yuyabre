import { useState, useEffect } from "react";
import * as Collapsible from "@radix-ui/react-collapsible";
import { Separator } from "./ui/Separator";
import { Button } from "./ui/Button";
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
import { Avatar } from "./ui/Avatar";
import { Tooltip } from "./ui/Tooltip";
import packageJson from "../../package.json";

interface SidebarButtonProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}

function SidebarButton({ icon, label, onClick }: SidebarButtonProps) {
  const { sidebarCollapsed } = useStore();

  const button = (
    <Button
      variant="ghost"
      size="2"
      onClick={onClick}
      className={`flex items-center gap-3 w-full justify-start ${
        sidebarCollapsed ? "justify-center px-2" : ""
      }`}
      aria-label={label}
    >
      <span className="flex-shrink-0 size-5 flex items-center justify-center">
        {icon}
      </span>
      {!sidebarCollapsed && <span className="flex-1 text-left">{label}</span>}
    </Button>
  );

  if (sidebarCollapsed) {
    return <Tooltip content={label}>{button}</Tooltip>;
  }

  return button;
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
    <Collapsible.Root
      open={!sidebarCollapsed}
      onOpenChange={(open) => {
        if (open !== !sidebarCollapsed) {
          toggleSidebar();
        }
      }}
      className={`flex flex-col h-screen bg-theme-secondary border-r border-theme-primary transition-all duration-200 ${
        sidebarCollapsed ? "w-16" : "w-64"
      }`}
    >
      {/* User Section as Header */}
      <div className="flex items-center justify-between p-3">
        {sidebarCollapsed ? (
          <Tooltip content="Expand sidebar">
            <Collapsible.Trigger asChild>
              <Button
                variant="ghost"
                size="2"
                className="flex items-center justify-center size-10"
                aria-label="Expand sidebar"
              >
                <IconChevronRight className="size-5" />
              </Button>
            </Collapsible.Trigger>
          </Tooltip>
        ) : (
          <>
            {currentUser ? (
              <>
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <Avatar
                    src={currentUser.avatar}
                    alt={currentUser.name}
                    fallback={<span>{getInitials(currentUser.name)}</span>}
                    className="flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-theme-primary truncate">
                      {currentUser.name}
                    </div>
                    <div className="text-xs text-theme-tertiary truncate">
                      {currentUser.email}
                    </div>
                  </div>
                </div>
                <Tooltip content="Collapse sidebar">
                  <Collapsible.Trigger asChild>
                    <Button
                      variant="ghost"
                      size="2"
                      className="flex items-center justify-center size-10 flex-shrink-0"
                      aria-label="Collapse sidebar"
                    >
                      <IconChevronLeft className="size-5" />
                    </Button>
                  </Collapsible.Trigger>
                </Tooltip>
              </>
            ) : (
              <>
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <Avatar fallback={<span>?</span>} className="flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-theme-primary">
                      Loading...
                    </div>
                    <div className="text-xs text-theme-tertiary">
                      Please wait
                    </div>
                  </div>
                </div>
                <Tooltip content="Collapse sidebar">
                  <Collapsible.Trigger asChild>
                    <Button
                      variant="ghost"
                      size="2"
                      className="flex items-center justify-center size-10 flex-shrink-0"
                      aria-label="Collapse sidebar"
                    >
                      <IconChevronLeft className="size-5" />
                    </Button>
                  </Collapsible.Trigger>
                </Tooltip>
              </>
            )}
          </>
        )}
      </div>
      <Separator />

      {/* Group Section */}
      <Collapsible.Content>
        {currentGroup && (
          <>
            <div className="p-3">
              <Button
                variant="ghost"
                size="2"
                onClick={() => setGroupOpen(true)}
                className="flex items-center gap-2 w-full justify-start"
              >
                <IconUsers className="size-4 flex-shrink-0" />
                <span className="truncate">{currentGroup.name}</span>
              </Button>
            </div>
            <Separator />
          </>
        )}
      </Collapsible.Content>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2 flex flex-col gap-1">
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

      {/* Settings */}
      <Collapsible.Content>
        <Separator />
        <div className="p-2">
          <Button
            variant="ghost"
            size="2"
            className="flex items-center gap-3 w-full justify-start"
          >
            <IconSettings className="size-4 flex-shrink-0" />
            <span>Settings</span>
          </Button>
        </div>
      </Collapsible.Content>

      {/* Collapsed Settings */}
      {sidebarCollapsed && (
        <>
          <Separator />
          <div className="p-2">
            <Tooltip content="Settings">
              <Button
                variant="ghost"
                size="2"
                className="flex items-center justify-center size-10 w-full"
                aria-label="Settings"
              >
                <IconSettings className="size-5" />
              </Button>
            </Tooltip>
          </div>
        </>
      )}

      {/* Footer */}
      <Collapsible.Content>
        <Separator />
        <div className="p-4">
          <div className="text-xs text-center text-theme-tertiary font-medium">
            Yuyabre v{packageJson.version}
          </div>
        </div>
      </Collapsible.Content>

      {/* Modals */}
      <InventoryModal open={inventoryOpen} onOpenChange={setInventoryOpen} />
      <OrdersModal open={ordersOpen} onOpenChange={setOrdersOpen} />
      <ExpensesModal open={expensesOpen} onOpenChange={setExpensesOpen} />
      <GroupModal open={groupOpen} onOpenChange={setGroupOpen} />
    </Collapsible.Root>
  );
}
