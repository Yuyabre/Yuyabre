import * as React from "react";
import { useLogout } from "@/hooks/useLogout";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator as SidebarSeparator2,
  SidebarTrigger,
  useSidebar,
} from "../ui/sidebar";
import { Button } from "../ui/button";
import { useStore } from "../../store/useStore";
import {
  IconPackage,
  IconShoppingCart,
  IconCurrencyEuro,
  IconUsers,
  IconSettings,
  IconLogout,
} from "@tabler/icons-react";
import { User } from "./User";
import packageJson from "../../../package.json";
import { cn } from "../../lib/utils";

function SidebarSeparator({
  className,
  ...props
}: React.ComponentProps<typeof SidebarSeparator2>) {
  return <SidebarSeparator2 className={cn("!mx-0", className)} {...props} />;
}

export interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  inventoryOpen: boolean;
  setInventoryOpen: (open: boolean) => void;
  ordersOpen: boolean;
  setOrdersOpen: (open: boolean) => void;
  expensesOpen: boolean;
  setExpensesOpen: (open: boolean) => void;
  householdOpen: boolean;
  setHouseholdOpen: (open: boolean) => void;
}

export function AppSidebar({
  inventoryOpen,
  setInventoryOpen,
  ordersOpen,
  setOrdersOpen,
  expensesOpen,
  setExpensesOpen,
  householdOpen,
  setHouseholdOpen,
  ...props
}: AppSidebarProps) {
  const { currentHousehold } = useStore();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  const logout = useLogout();

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <div className="flex flex-row items-center gap-2 w-full">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={logout}
          >
            <IconLogout className="size-4" />
            <span className="sr-only">Log out</span>
          </Button>
          <SidebarTrigger className="ml-auto" />
        </div>
        <SidebarSeparator />
        <User />
      </SidebarHeader>

      <SidebarContent>
        {/* Group Section */}
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip={currentHousehold ? currentHousehold.name : "Household setup"}
                onClick={() => {
                  if (currentHousehold) {
                    setHouseholdOpen(true);
                  }
                }}
              >
                <IconUsers className="size-4" />
                <span>{currentHousehold ? currentHousehold.name : "Set up household"}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>

        <SidebarSeparator />

        {/* Navigation */}
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip="Inventory"
                onClick={() => setInventoryOpen(true)}
              >
                <IconPackage className="size-4" />
                <span>Inventory</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip="Orders"
                onClick={() => setOrdersOpen(true)}
              >
                <IconShoppingCart className="size-4" />
                <span>Orders</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip="Expenses"
                onClick={() => setExpensesOpen(true)}
              >
                <IconCurrencyEuro className="size-4" />
                <span>Expenses</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="!px-0">
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
        <div
          className={cn(
            "transition-all duration-200 overflow-hidden",
            isCollapsed ? "max-h-0 opacity-0" : "max-h-20 opacity-100"
          )}
        >
          <SidebarSeparator />
        </div>
        <div
          className={cn(
            "px-2 py-1.5 transition-all duration-200 overflow-hidden",
            isCollapsed ? "max-h-0 opacity-0 py-0" : "max-h-20 opacity-100"
          )}
        >
          <div className="text-xs text-center text-muted-foreground font-medium">
            Yuyabre v{packageJson.version}
          </div>
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
