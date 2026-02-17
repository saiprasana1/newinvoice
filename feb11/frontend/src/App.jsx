import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Welcome from "./pages/Welcome";
import Home from "./pages/Home";
import BillInvoice from "./pages/BillInvoice";
import TaxInvoice from "./pages/TaxInvoice";
import { InvoiceProvider } from "./context/InvoiceContext";
import Services from "./pages/Services";
import Login from "./pages/Login";
import ProtectedRoute from "./components/ProtectedRoute";
import Guidance from "./pages/Guidance";


function App() {
  return (
    <InvoiceProvider>
      <Router>
        <Routes>

  <Route path="/" element={<Welcome />} />
  <Route path="/services" element={<Services />} />

  <Route path="/login" element={<Login />} />

  <Route
    path="/dashboard"
    element={
      <Layout>
        <Home />
      </Layout>
    }
  />

  <Route
    path="/bill-invoice"
    element={
      <ProtectedRoute>
        <Layout>
          <BillInvoice />
        </Layout>
      </ProtectedRoute>
    }
  />

    <Route path="/guidance" element={<Guidance />} />

  <Route
    path="/tax-invoice"
    element={
      <ProtectedRoute>
        <Layout>
          <TaxInvoice />
        </Layout>
      </ProtectedRoute>
    }
  />

</Routes>

      </Router>
    </InvoiceProvider>
  );
}

export default App;
