import Sidebar from "./components/basic/Sidebar";
import Chat from "./components/layouts/Chat";
import { WebSocketProvider } from "./providers/WebSocketProvider";
import { ThemeProvider } from "./components/basic/ThemeProvider";
import { SidebarProvider, SidebarInset } from "./components/ui/sidebar";
import "./App.css";
import { Toaster } from "sonner";

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="yuyabre-theme">
      <WebSocketProvider>
        <SidebarProvider>
          <div className="app flex">
            <Sidebar />
            <SidebarInset className="flex-1">
              <main className="app-main">
                <Toaster position="top-right" richColors />
                <Chat />
              </main>
            </SidebarInset>
          </div>
        </SidebarProvider>
      </WebSocketProvider>
    </ThemeProvider>
  );
}

export default App;
