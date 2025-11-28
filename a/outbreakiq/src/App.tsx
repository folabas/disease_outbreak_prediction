import { Routes, Route, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { ErrorBoundary } from "./Components/ErrorBoundary";
import Layout from "./Components/Layout";
import Home from "./pages/Home";
import Predictions from "./pages/Predictions";
import Climate from "./pages/Climate";
import Population from "./pages/Population";
import Hospital from "./pages/Hospital";
import Insights from "./pages/Insights";
import { useDashboardStore } from "./store/useDashboardStore";

const AppContent = () => {
  const location = useLocation();
  const { syncFromUrl } = useDashboardStore();

  // Only sync FROM URL on route change (don't add params to all routes)
  useEffect(() => {
    syncFromUrl();
  }, [location.pathname, syncFromUrl]);

  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/predictions" element={<ErrorBoundary><Predictions /></ErrorBoundary>} />
          <Route path="/climate" element={<ErrorBoundary><Climate /></ErrorBoundary>} />
          <Route path="/population" element={<ErrorBoundary><Population /></ErrorBoundary>} />
          <Route path="/hospital" element={<ErrorBoundary><Hospital /></ErrorBoundary>} />
          <Route path="/insights" element={<ErrorBoundary><Insights /></ErrorBoundary>} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
};

const App = () => {
  return <AppContent />;
};

export default App;
