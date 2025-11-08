import { AppSidebar } from "./components/basic/Sidebar";
import Chat from "./components/layouts/Chat";
import { WebSocketProvider } from "./providers/WebSocketProvider";
import { ThemeProvider } from "./components/basic/ThemeProvider";
import { SidebarProvider, SidebarInset } from "./components/ui/sidebar";
import "./App.css";
import { Toaster } from "sonner";
import { InventoryModal } from "./components/modals/InventoryModal";
import { ExpensesModal } from "./components/modals/ExpensesModal";
import { useState } from "react";
import { OrdersModal } from "./components/modals/OrdersModal";
import { GroupModal } from "./components/modals/GroupModal";
import { Header } from "./components/basic/Header";

function App() {
  const [inventoryOpen, setInventoryOpen] = useState(false);
  const [ordersOpen, setOrdersOpen] = useState(false);
  const [expensesOpen, setExpensesOpen] = useState(false);
  const [groupOpen, setGroupOpen] = useState(false);

  return (
    <ThemeProvider defaultTheme="system" storageKey="yuyabre-theme">
      <WebSocketProvider>
        <SidebarProvider>
          <AppSidebar
            inventoryOpen={inventoryOpen}
            setInventoryOpen={setInventoryOpen}
            ordersOpen={ordersOpen}
            setOrdersOpen={setOrdersOpen}
            expensesOpen={expensesOpen}
            setExpensesOpen={setExpensesOpen}
            groupOpen={groupOpen}
            setGroupOpen={setGroupOpen}
          />
          <SidebarInset>
            <div className="flex flex-1 flex-col gap-4 p-4">
              <Header />
              <Chat />
            </div>
          </SidebarInset>
        </SidebarProvider>
        <Toaster position="top-right" richColors />
        <InventoryModal open={inventoryOpen} onOpenChange={setInventoryOpen} />
        <OrdersModal open={ordersOpen} onOpenChange={setOrdersOpen} />
        <ExpensesModal open={expensesOpen} onOpenChange={setExpensesOpen} />
        <GroupModal open={groupOpen} onOpenChange={setGroupOpen} />
      </WebSocketProvider>
    </ThemeProvider>
  );
}

export default App;
