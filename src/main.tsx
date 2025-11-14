// 🔥 StrictMode temporarily disabled - see createRoot call below
// import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// Initialize axe-core for accessibility testing in development
// Temporarily disabled - restart dev server to enable
// if (import.meta.env.DEV) {
//   import('@axe-core/react').then((axe) => {
//     axe.default(StrictMode, createRoot, 1000, {
//       rules: [
//         // You can configure specific rules here if needed
//         // { id: 'rule-id', enabled: false }
//       ]
//     });
//   }).catch((error) => {
//     console.error('Failed to load axe-core:', error);
//   });
// }

createRoot(document.getElementById("root")!).render(
  // 🔥 TEMPORARILY DISABLED StrictMode to fix infinite re-renders
  // TODO: Re-enable after adding proper ref-based initialization guards
  // <StrictMode>
    <App />
  // </StrictMode>
);
