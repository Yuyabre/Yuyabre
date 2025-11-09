import { toast } from "sonner";
import { useStore } from "@/store/useStore";
import { authStorage } from "@/lib/authStorage";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "../ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { IconChevronDown } from "@tabler/icons-react";

export function User() {
  const { currentUser, setCurrentUser, setCurrentHousehold } = useStore();

  if (!currentUser) {
    return null;
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((segment) => segment.charAt(0))
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const handleLogout = () => {
    authStorage.clear();
    setCurrentUser(null);
    setCurrentHousehold(null);
    toast.success("Logged out");
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="w-full data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <Avatar className="flex-shrink-0">
                <AvatarFallback>{getInitials(currentUser.name)}</AvatarFallback>
              </Avatar>
              <div className="flex flex-col gap-0.5 leading-none text-left">
                <span className="font-medium truncate">{currentUser.name}</span>
                {currentUser.email && (
                  <span className="text-xs text-muted-foreground truncate">
                    {currentUser.email}
                  </span>
                )}
              </div>
              <IconChevronDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width)"
            align="start"
          >
            <DropdownMenuItem onClick={handleLogout}>
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
