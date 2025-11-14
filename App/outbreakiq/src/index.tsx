import { createRoot } from "react-dom/client";
import "./index.css";
// Ensure Leaflet's CSS is loaded globally. Some components also import it, but
// having it at the entry guarantees map styles are available early.
import "leaflet/dist/leaflet.css";
import App from "./App";
import { BrowserRouter } from "react-router-dom";

// Create root with strict mode for development
const root = createRoot(document.getElementById("root") as HTMLElement);

root.render(
  <BrowserRouter
    future={{
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    }}
  >
    <App />
  </BrowserRouter>
);
