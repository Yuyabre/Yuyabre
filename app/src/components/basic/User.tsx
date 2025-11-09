import { useStore } from "@/store/useStore";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { SidebarMenu, SidebarMenuItem } from "../ui/sidebar";

export function User() {
  const { currentUser } = useStore();

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

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <div className="flex w-full items-center gap-3 rounded-md bg-transparent p-2 text-left text-sm">
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
        </div>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
