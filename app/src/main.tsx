import React from "react";
import ReactDOM from "react-dom/client";
import { registerSW } from "virtual:pwa-register";
import { QueryProvider } from "./providers/QueryProvider";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryProvider>
      <App />
    </QueryProvider>
  </React.StrictMode>
);

registerSW({
  immediate: true,
  onRegisteredSW(swUrl: string, registration?: ServiceWorkerRegistration) {
    if (import.meta.env.DEV) {
      console.info("Service worker registered:", swUrl, registration);
    }
  },
  onRegisterError(error: Error) {
    console.error("Service worker registration failed:", error);
  },
});
