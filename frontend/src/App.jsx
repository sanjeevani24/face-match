import { Routes, Route, Navigate } from "react-router-dom";
import DashboardLayout from "./components/layout/DashboardLayout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Verification from "./pages/Verification.jsx";
import FaceMatchCheck from "./pages/FaceMatchCheck.jsx";
import History from "./pages/History.jsx";
import Logs from "./pages/Logs.jsx";
import OfficerCall from "./pages/OfficerCall.jsx";
import CustomerCall from "./pages/CustomerCall.jsx";
import CallSessionTest from "./pages/CallSessionTest.jsx";
import CallReportView from "./pages/CallReportView";

export default function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/verification" element={<Verification />} />
        <Route path="/face-match" element={<FaceMatchCheck />} />
        <Route path="/history" element={<History />} />
        <Route path="/logs" element={<Logs />} />
        {/* Officer is internal staff -- keep the dashboard chrome. */}
        <Route path="/officer/call" element={<OfficerCall />} />
        {/* Internal test harness for creating call sessions -- dashboard chrome is fine here too. */}
        <Route path="/call-test" element={<CallSessionTest />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>

      {/* Customer is an external applicant -- no sidebar/header. */}
      <Route path="/customer/call" element={<CustomerCall />} />
      <Route path="/report/:roomId" element={<CallReportView />} />
    </Routes>
  );
}
