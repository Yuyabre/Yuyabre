import Sidebar from "./components/Sidebar";
import Chat from "./components/layouts/Chat";
import "./App.css";
import { Toaster } from "sonner";

function App() {
  return (
    <div className="app">
      <Sidebar />
      <main className="app-main">
        <Toaster position="top-right" richColors />
        <Chat />
      </main>
    </div>
  );
}

export default App;
