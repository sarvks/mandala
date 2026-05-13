import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Landing from "./pages/Landing";
import Deities from "./pages/Deities";
import DeityDetail from "./pages/DeityDetail";
import Temples from "./pages/Temples";
import Donate from "./pages/Donate";
import Subscribe from "./pages/Subscribe";
import Patron from "./pages/Patron";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import AdminDashboard from "./pages/AdminDashboard";
import TempleAdmin from "./pages/TempleAdmin";
import Traditions from "./pages/Traditions";
import Causes from "./pages/Causes";
import CauseDetail from "./pages/CauseDetail";
import CauseDonate from "./pages/CauseDonate";
import CauseSubscribe from "./pages/CauseSubscribe";
import Partner from "./pages/Partner";
import "./App.css";

function App() {
  return (
    <div className="App mandala-paper min-h-screen">
      <AuthProvider>
        <BrowserRouter>
          <Navbar />
          <main data-testid="main-content">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/deities" element={<Deities />} />
              <Route path="/deities/:id" element={<DeityDetail />} />
              <Route path="/temples" element={<Temples />} />
              <Route path="/donate/:deityId" element={<Donate />} />
              <Route path="/subscribe/:deityId" element={<Subscribe />} />
              <Route path="/patron" element={<Patron />} />
              <Route path="/traditions" element={<Traditions />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/temple-admin" element={<TempleAdmin />} />
              <Route path="/partner" element={<Partner />} />
              <Route path="/causes" element={<Causes />} />
              <Route path="/causes/category/:category" element={<Causes />} />
              <Route path="/causes/:id" element={<CauseDetail />} />
              <Route path="/cause-donate/:causeId" element={<CauseDonate />} />
              <Route path="/cause-subscribe/:causeId" element={<CauseSubscribe />} />
            </Routes>
          </main>
          <Footer />
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
