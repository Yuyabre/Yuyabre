import { useState, useEffect } from "react";
import { Theme } from "@radix-ui/themes";
import Sidebar from "./components/Sidebar";
import Chat from "./components/layouts/Chat";
import { WebSocketProvider } from "./providers/WebSocketProvider";
import { TooltipProvider } from "./components/ui/Tooltip";
import "./App.css";
import { Toaster } from "sonner";

function App() {
  const [appearance, setAppearance] = useState<"light" | "dark">("light");

  useEffect(() => {
    // Detect system preference
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    setAppearance(mediaQuery.matches ? "dark" : "light");

    // Listen for changes
    const handleChange = (e: MediaQueryListEvent) => {
      setAppearance(e.matches ? "dark" : "light");
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  useEffect(() => {
    // Set data-theme attribute on document root for CSS variable switching
    document.documentElement.setAttribute("data-theme", appearance);
  }, [appearance]);

  return (
    <Theme
      appearance={appearance}
      accentColor="gray"
      grayColor="slate"
      radius="medium"
      scaling="100%"
    >
      <WebSocketProvider>
        <TooltipProvider>
          <div className="app">
            <Sidebar />
            <main className="app-main">
              <Toaster position="top-right" richColors />
              <Chat />
            </main>
          </div>
        </TooltipProvider>
      </WebSocketProvider>
    </Theme>
  );
}

export default App;
