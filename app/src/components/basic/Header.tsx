import { SidebarTrigger } from "../ui/sidebar";

export function Header() {
  return (
    <header className="flex h-12 shrink-0 gap-2">
      <SidebarTrigger className="-ml-1" />
    </header>
  );
}
