import Sidebar from "./components/Sidebar";
import Chat from "./components/layouts/Chat";
import { WebSocketProvider } from "./providers/WebSocketProvider";
import "./App.css";
import { Toaster } from "sonner";

function App() {
  return (
    <WebSocketProvider>
      <div className="app">
        <Sidebar />
        <main className="app-main">
          <Toaster position="top-right" richColors />
          <Chat />
        </main>
      </div>
    </WebSocketProvider>
  );
}

export default App;
