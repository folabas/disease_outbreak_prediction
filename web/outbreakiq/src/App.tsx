import { Routes, Route } from "react-router-dom";
import Layout from "./Components/Layout";
import Home from "./pages/Home";
import Predictions from "./pages/Predictions";
import Climate from "./pages/Climate";
import Population from "./pages/Population";
import Hospital from "./pages/Hospital";
import Insights from "./pages/Insights";

const App = () => {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/predictions" element={<Predictions />} />
        <Route path="/climate" element={<Climate />} />
        <Route path="/population" element={<Population />} />
        <Route path="/hospital" element={<Hospital />} />
        <Route path="/insights" element={<Insights />} />
      </Route>
    </Routes>
  );
};

export default App;
