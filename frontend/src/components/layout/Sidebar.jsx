import { NavLink } from "react-router-dom";
import { LayoutDashboard, ScanFace, History as HistoryIcon, ShieldCheck, UserCheck, FileText } from "lucide-react";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/verification", label: "Verification", icon: ScanFace },
  { to: "/face-match", label: "Face Match Check", icon: UserCheck },
  { to: "/history", label: "History", icon: HistoryIcon },
  { to: "/logs", label: "Logs", icon: FileText },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/30 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 shrink-0 border-r border-[var(--color-border)] bg-[var(--color-brand-blue)] text-white transition-transform duration-200 lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center gap-2.5 px-6">
          <div className="flex size-9 items-center justify-center rounded-lg bg-white/10">
            <ShieldCheck className="size-5 text-[var(--color-brand-green-light)]" />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-bold">Finance</p>
            <p className="text-[11px] text-white/60">eKYC Console</p>
          </div>
        </div>

        <nav className="mt-4 flex flex-col gap-1 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? "bg-white text-[var(--color-brand-blue)]" : "text-white/80 hover:bg-white/10"
                }`
              }
            >
              <Icon className="size-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full border-t border-white/10 p-4">
          <p className="text-[11px] text-white/50">
            Aadhaar-based eKYC · InsightFace + MediaPipe
          </p>
        </div>
      </aside>
    </>
  );
}
