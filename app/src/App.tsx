import { useEffect, useState } from "react";
import { AppSidebar } from "./components/basic/Sidebar";
import Chat from "./components/layouts/Chat";
import { WebSocketProvider } from "./providers/WebSocketProvider";
import { ThemeProvider } from "./components/basic/ThemeProvider";
import { SidebarProvider, SidebarInset } from "./components/ui/sidebar";
import "./App.css";
import { Toaster } from "sonner";
import { InventoryModal } from "./components/modals/InventoryModal";
import { ExpensesModal } from "./components/modals/ExpensesModal";
import { OrdersModal } from "./components/modals/OrdersModal";
import { HouseholdModal } from "./components/modals/HouseholdModal";
import { HouseholdOnboardingModal } from "./components/modals/HouseholdOnboardingModal";
import { Header } from "./components/basic/Header";
import { AuthScreen } from "./components/layouts/Auth/AuthScreen";
import { useStore } from "./store/useStore";
import { authStorage } from "./lib/authStorage";
import { useGetHousehold, useGetUser } from "./lib/queries";

function App() {
  const [inventoryOpen, setInventoryOpen] = useState(false);
  const [ordersOpen, setOrdersOpen] = useState(false);
  const [expensesOpen, setExpensesOpen] = useState(false);
  const [householdOpen, setHouseholdOpen] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const [hasPromptedHousehold, setHasPromptedHousehold] = useState(false);
  const { currentUser, setCurrentUser, setCurrentHousehold } = useStore();

  // Fetch latest user info when we have a user_id
  const { data: fetchedUser, isLoading: isLoadingUser } = useGetUser(
    currentUser?.user_id ?? null
  );

  // Fetch household when user has household_id
  const { data: fetchedHousehold, isLoading: isLoadingHousehold } = useGetHousehold(
    currentUser?.household_id ?? null
  );

  useEffect(() => {
    const storedUser = authStorage.loadUser();
    if (storedUser) {
      setCurrentUser(storedUser);
    }
    setIsHydrated(true);
  }, [setCurrentUser]);

  // Update user when fetched from API
  useEffect(() => {
    if (fetchedUser) {
      setCurrentUser(fetchedUser);
      authStorage.saveUser(fetchedUser);
    }
  }, [fetchedUser, setCurrentUser]);

  // Update household when fetched
  useEffect(() => {
    if (fetchedHousehold) {
      setCurrentHousehold(fetchedHousehold);
      authStorage.saveHousehold(fetchedHousehold);
    } else if (currentUser && !currentUser.household_id) {
      // Clear household if user has no household_id
      setCurrentHousehold(null);
      authStorage.saveHousehold(null);
    }
  }, [fetchedHousehold, currentUser, setCurrentHousehold]);

  useEffect(() => {
    if (!currentUser) {
      setHasPromptedHousehold(false);
      return;
    }

    // Only show onboarding modal if user has no household_id
    // Don't show if household is still loading
    if (
      !currentUser.household_id &&
      !hasPromptedHousehold &&
      !isLoadingUser &&
      !isLoadingHousehold
    ) {
      setHasPromptedHousehold(true);
    } else if (currentUser.household_id && hasPromptedHousehold) {
      // Reset flag when user has household_id
      setHasPromptedHousehold(false);
    }
  }, [
    currentUser,
    hasPromptedHousehold,
    isLoadingHousehold,
    isLoadingUser,
  ]);

  if (!isHydrated) {
    return null;
  }

  if (!currentUser) {
    return (
      <ThemeProvider defaultTheme="system" storageKey="yuyabre-theme">
        <Toaster position="top-right" richColors />
        <AuthScreen />
      </ThemeProvider>
    );
  }

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
            householdOpen={householdOpen}
            setHouseholdOpen={setHouseholdOpen}
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
        <HouseholdModal open={householdOpen} onOpenChange={setHouseholdOpen} />
        {currentUser && !currentUser.household_id && !isLoadingUser && (
          <HouseholdOnboardingModal open={hasPromptedHousehold} />
        )}
      </WebSocketProvider>
    </ThemeProvider>
  );
}

export default App;
