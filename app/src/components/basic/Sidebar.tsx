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
  IconDeviceMobileCheck,
} from "@tabler/icons-react";
import { User } from "./User";
import packageJson from "../../../package.json";
import { cn } from "../../lib/utils";

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: "accepted" | "dismissed";
    platform: string;
  }>;
  prompt: () => Promise<void>;
}

declare global {
  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
  }
}

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
  settingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;
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
  settingsOpen,
  setSettingsOpen,
  ...props
}: AppSidebarProps) {
  const { currentHousehold } = useStore();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  const logout = useLogout();
  const [installPrompt, setInstallPrompt] =
    React.useState<BeforeInstallPromptEvent | null>(null);
  const [canInstall, setCanInstall] = React.useState(false);

  React.useEffect(() => {
    const handleBeforeInstallPrompt = (event: BeforeInstallPromptEvent) => {
      event.preventDefault();
      setInstallPrompt(event);
      setCanInstall(true);
      console.log("Before install prompt");
    };

    const handleAppInstalled = () => {
      setInstallPrompt(null);
      setCanInstall(false);
      console.log("App installed");
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    if (
      window.matchMedia("(display-mode: standalone)").matches ||
      (navigator as Navigator & { standalone?: boolean }).standalone
    ) {
      console.log("App is installed (standalone)");
      setCanInstall(false);
    }

    return () => {
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt
      );
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  const handleInstallClick = React.useCallback(async () => {
    if (!installPrompt) {
      return;
    }

    try {
      await installPrompt.prompt();
      await installPrompt.userChoice;
    } finally {
      console.log("Install prompt user choice");
      setInstallPrompt(null);
      setCanInstall(false);
    }
  }, [installPrompt]);

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
          {canInstall && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleInstallClick}
              disabled={!installPrompt}
            >
              <IconDeviceMobileCheck className="size-4" />
              <span className="sr-only">Install app</span>
            </Button>
          )}
          <SidebarTrigger className="ml-auto" />
        </div>
        <User />
      </SidebarHeader>

      <SidebarContent>
        {/* Group Section */}
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip={
                  currentHousehold ? currentHousehold.name : "Household setup"
                }
                onClick={() => {
                  if (currentHousehold) {
                    setHouseholdOpen(true);
                  }
                }}
              >
                <IconUsers className="size-4" />
                <span>
                  {currentHousehold
                    ? currentHousehold.name
                    : "Set up household"}
                </span>
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
              <SidebarMenuButton
                tooltip="Settings"
                onClick={() => setSettingsOpen(true)}
              >
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
