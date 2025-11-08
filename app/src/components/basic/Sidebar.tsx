import { useState, useEffect } from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
  SidebarTrigger,
  useSidebar,
} from "../ui/sidebar";
import { useStore } from "../../store/useStore";
import {
  IconChevronLeft,
  IconChevronRight,
  IconPackage,
  IconShoppingCart,
  IconCurrencyEuro,
  IconUsers,
  IconSettings,
} from "@tabler/icons-react";
import { userApi } from "../../lib/api";
import { InventoryModal } from "../modals/InventoryModal";
import { OrdersModal } from "../modals/OrdersModal";
import { ExpensesModal } from "../modals/ExpensesModal";
import { GroupModal } from "../modals/GroupModal";
import { Avatar, AvatarImage, AvatarFallback } from "../ui/avatar";
import packageJson from "../../../package.json";

function Separator() {
  return <SidebarSeparator className="!mx-0" />;
}

function AppSidebar() {
  const { currentUser, currentGroup, setCurrentUser, setCurrentGroup } =
    useStore();

  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

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
    <Sidebar collapsible="icon">
      <SidebarHeader className="p-3 flex-shrink-0">
        <div className="flex items-center justify-between w-full gap-2">
          {currentUser ? (
            <>
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <Avatar className="flex-shrink-0">
                  <AvatarImage
                    src={currentUser.avatar}
                    alt={currentUser.name}
                  />
                  <AvatarFallback>
                    {getInitials(currentUser.name)}
                  </AvatarFallback>
                </Avatar>
                {!isCollapsed && (
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-foreground truncate">
                      {currentUser.name}
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                      {currentUser.email}
                    </div>
                  </div>
                )}
              </div>
              <SidebarTrigger className="h-10 w-10 flex-shrink-0">
                {isCollapsed ? (
                  <IconChevronRight className="size-5" />
                ) : (
                  <IconChevronLeft className="size-5" />
                )}
              </SidebarTrigger>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <Avatar className="flex-shrink-0">
                  <AvatarFallback>?</AvatarFallback>
                </Avatar>
                {!isCollapsed && (
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-foreground">
                      Loading...
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Please wait
                    </div>
                  </div>
                )}
              </div>
              <SidebarTrigger className="h-10 w-10 flex-shrink-0">
                {isCollapsed ? (
                  <IconChevronRight className="size-5" />
                ) : (
                  <IconChevronLeft className="size-5" />
                )}
              </SidebarTrigger>
            </>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        {/* Group Section */}
        {currentGroup && (
          <SidebarGroup>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  tooltip={currentGroup.name}
                  onClick={() => setGroupOpen(true)}
                >
                  <IconUsers className="size-4" />
                  <span>{currentGroup.name}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroup>
        )}

        <Separator />

        {/* Navigation */}
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip="Inventory"
                onClick={() => setInventoryOpen(true)}
              >
                <IconPackage className="size-5" />
                <span>Inventory</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip="Orders"
                onClick={() => setOrdersOpen(true)}
              >
                <IconShoppingCart className="size-5" />
                <span>Orders</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip="Expenses"
                onClick={() => setExpensesOpen(true)}
              >
                <IconCurrencyEuro className="size-5" />
                <span>Expenses</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="flex-shrink-0 !px-0">
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton tooltip="Settings">
                <IconSettings className="size-4" />
                <span>Settings</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
        <Separator />
        <div className="p-2">
          <div className="text-xs text-center text-muted-foreground font-medium">
            Yuyabre v{packageJson.version}
          </div>
        </div>
      </SidebarFooter>

      {/* Modals */}
      <InventoryModal open={inventoryOpen} onOpenChange={setInventoryOpen} />
      <OrdersModal open={ordersOpen} onOpenChange={setOrdersOpen} />
      <ExpensesModal open={expensesOpen} onOpenChange={setExpensesOpen} />
      <GroupModal open={groupOpen} onOpenChange={setGroupOpen} />
    </Sidebar>
  );
}

export default AppSidebar;
