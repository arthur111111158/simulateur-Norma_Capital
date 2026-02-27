import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import QuotePage from "./pages/QuotePage";
import NewsPage from "./pages/NewsPage";
import WorldMapPage from "./pages/WorldMapPage";
import SupplyChainPage from "./pages/SupplyChainPage";
import ScreenerPage from "./pages/ScreenerPage";
import SettingsPage from "./pages/SettingsPage";
import EarningsPage from "./pages/EarningsPage";
import CommoditiesPage from "./pages/CommoditiesPage";
import ForexPage from "./pages/ForexPage";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/quote" element={<QuotePage />} />
            <Route path="/news" element={<NewsPage />} />
            <Route path="/worldmap" element={<WorldMapPage />} />
            <Route path="/supplychain" element={<SupplyChainPage />} />
            <Route path="/screener" element={<ScreenerPage />} />
            <Route path="/earnings" element={<EarningsPage />} />
            <Route path="/commodities" element={<CommoditiesPage />} />
            <Route path="/forex" element={<ForexPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Layout>
        <Toaster />
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
