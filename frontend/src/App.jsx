import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { ToastProvider } from "./components/Toast";
import AddContact from "./pages/AddContact";
import Overview from "./pages/Overview";
import Outreach from "./pages/Outreach";
import Replies from "./pages/Replies";
import Suppression from "./pages/Suppression";
import Templates from "./pages/Templates";

const NAV = [
  { id: "Overview", label: "Overview", icon: "◧" },
  { id: "Add", label: "Add recruiter", icon: "+" },
  { id: "Outreach", label: "Outreach", icon: "✦", badge: "pending_approval" },
  { id: "Replies", label: "Replies", icon: "✉", badge: "needs_review" },
  { id: "Templates", label: "Templates", icon: "▤" },
  { id: "Suppression", label: "Suppression", icon: "⊘" },
];

const SUBTITLES = {
  Overview: "Where everything stands at a glance.",
  Add: "Add a recruiter and generate the draft.",
  Outreach: "Approvals, the scheduled queue, and your sent log.",
  Replies: "Review detected replies and label them.",
  Templates: "Your outreach templates.",
  Suppression: "Addresses that must never be emailed.",
};

export default function App() {
  const [tab, setTab] = useState("Overview");
  const [templates, setTemplates] = useState([]);
  const [stats, setStats] = useState({});
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);
  const loadTemplates = useCallback(() => {
    api.listTemplates().then(setTemplates).catch(() => setTemplates([]));
  }, []);
  const loadStats = useCallback(() => {
    api.stats().then(setStats).catch(() => {});
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  // refresh stats on every action + poll every 20s so the dashboard stays live
  useEffect(() => {
    loadStats();
    const id = setInterval(() => {
      loadStats();
      setRefreshKey((k) => k + 1);
    }, 20000);
    return () => clearInterval(id);
  }, [loadStats, refreshKey]);

  return (
    <ToastProvider>
      <div className="min-h-screen flex">
        {/* ── Sidebar ── */}
        <aside className="hidden md:flex w-60 shrink-0 flex-col bg-brand-sidebar border-r border-brand-line">
          <div className="px-6 py-6">
            <span className="text-2xl font-bold text-brand-blue">{"<Ved/>"}</span>
            <div className="text-xs text-brand-muted mt-1">Recruiter Outreach</div>
          </div>

          <nav className="px-3 space-y-1">
            {NAV.map((n) => {
              const active = tab === n.id;
              const badge = n.badge ? stats[n.badge] : 0;
              return (
                <button
                  key={n.id}
                  onClick={() => setTab(n.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                    active
                      ? "bg-brand-blue text-white shadow-blue"
                      : "text-brand-muted hover:text-brand-ink hover:bg-brand-panel2"
                  }`}
                >
                  <span className="w-5 text-center opacity-90">{n.icon}</span>
                  <span className="flex-1 text-left">{n.label}</span>
                  {badge > 0 && (
                    <span
                      className={`text-[10px] font-bold rounded-full min-w-[18px] h-[18px] px-1 inline-flex items-center justify-center ${
                        active ? "bg-white/25" : "bg-brand-blue text-white"
                      }`}
                    >
                      {badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          <div className="mt-auto px-6 py-5 border-t border-brand-line">
            <div className="text-sm font-medium text-brand-ink">Ved Prakash Meena</div>
            <div className="text-xs text-brand-muted truncate">connect.ved21@gmail.com</div>
          </div>
        </aside>

        {/* ── Main column ── */}
        <div className="flex-1 min-w-0 bg-brand-bg flex flex-col">
          {/* topbar */}
          <header className="sticky top-0 z-10 bg-brand-panel/95 backdrop-blur border-b border-brand-line">
            <div className="px-5 sm:px-8 py-4 flex items-center justify-between">
              <div>
                <h1 className="text-xl font-semibold text-brand-ink">
                  {NAV.find((n) => n.id === tab)?.label}
                </h1>
                <p className="text-sm text-brand-muted">{SUBTITLES[tab]}</p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={api.exportCsvUrl()}
                  className="text-sm font-semibold px-4 py-2 rounded-lg border border-brand-line text-brand-muted hover:text-brand-ink hover:bg-brand-panel2 transition"
                >
                  Export CSV
                </a>
                <button
                  onClick={() => setTab("Add")}
                  className="bg-brand-blue text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-blue hover:-translate-y-0.5 transition"
                >
                  + Add recruiter
                </button>
              </div>
            </div>
            {/* mobile nav */}
            <div className="md:hidden px-3 pb-2 flex gap-1 overflow-x-auto">
              {NAV.map((n) => (
                <button
                  key={n.id}
                  onClick={() => setTab(n.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap ${
                    tab === n.id ? "bg-brand-blue text-white" : "text-brand-muted bg-brand-panel2"
                  }`}
                >
                  {n.label}
                </button>
              ))}
            </div>
          </header>

          <main className="p-5 sm:p-8 flex-1">
            {tab === "Overview" && <Overview refreshKey={refreshKey} goTo={setTab} />}
            {tab === "Add" && <AddContact templates={templates} onAdded={refresh} />}
            {tab === "Outreach" && (
              <Outreach refreshKey={refreshKey} onChange={refresh} stats={stats} />
            )}
            {tab === "Replies" && (
              <Replies refreshKey={refreshKey} onChange={refresh} stats={stats} />
            )}
            {tab === "Templates" && (
              <Templates templates={templates} onChange={loadTemplates} />
            )}
            {tab === "Suppression" && <Suppression refreshKey={refreshKey} />}
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
