import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { ToastProvider } from "./components/Toast";
import {
  IconBlock,
  IconColumns,
  IconGrid,
  IconList,
  IconMail,
  IconPlus,
  IconSend,
  IconSettings,
} from "./components/icons";
import AddContact from "./pages/AddContact";
import Board from "./pages/Board";
import Overview from "./pages/Overview";
import Outreach from "./pages/Outreach";
import Replies from "./pages/Replies";
import Settings from "./pages/Settings";
import Suppression from "./pages/Suppression";
import Templates from "./pages/Templates";

const NAV = [
  { id: "Overview", label: "Overview", Icon: IconGrid },
  { id: "Add", label: "New email", Icon: IconPlus },
  { id: "Board", label: "Pipeline", Icon: IconColumns },
  { id: "Outreach", label: "Outreach", Icon: IconSend, badge: "pending_approval" },
  { id: "Replies", label: "Replies", Icon: IconMail, badge: "needs_review" },
  { id: "Templates", label: "Templates", Icon: IconList },
  { id: "Suppression", label: "Suppression", Icon: IconBlock },
  { id: "Settings", label: "Settings", Icon: IconSettings },
];

function initials(name) {
  if (!name?.trim()) return "?";
  const parts = name.trim().split(/\s+/);
  return (parts[0][0] + (parts[1]?.[0] || "")).toUpperCase();
}

const SUBTITLES = {
  Overview: "Where everything stands at a glance.",
  Add: "Pick a template, fill the fields, and queue the email.",
  Board: "Every thread, laid out by where it stands.",
  Outreach: "Approvals, the scheduled queue, and your sent log.",
  Replies: "Review detected replies and label them.",
  Templates: "Your outreach templates.",
  Suppression: "Addresses that must never be emailed.",
  Settings: "Timezone, send windows, and working days.",
};

export default function App() {
  const [tab, setTab] = useState("Overview");
  const [templates, setTemplates] = useState([]);
  const [stats, setStats] = useState({});
  const [me, setMe] = useState({ sender_name: "" });
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
    api.getSettings().then(setMe).catch(() => {});
  }, [loadTemplates, refreshKey]);

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
          <div className="px-6 py-7">
            <span className="text-[22px] font-extrabold text-brand-blue tracking-tight">✉ Mailflow</span>
            <div className="text-xs text-brand-muted mt-1">Email Automation</div>
          </div>

          <nav className="px-3 space-y-0.5">
            {NAV.map((n) => {
              const active = tab === n.id;
              const badge = n.badge ? stats[n.badge] : 0;
              return (
                <button
                  key={n.id}
                  onClick={() => setTab(n.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                    active
                      ? "bg-brand-blueSoft text-brand-blue"
                      : "text-brand-muted hover:text-brand-ink hover:bg-brand-panel2"
                  }`}
                >
                  <n.Icon className="shrink-0" />
                  <span className="flex-1 text-left">{n.label}</span>
                  {badge > 0 && (
                    <span className="text-[10px] font-bold rounded-full min-w-[18px] h-[18px] px-1 inline-flex items-center justify-center bg-brand-blue text-white">
                      {badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          <button
            onClick={() => setTab("Settings")}
            className="mt-auto flex items-center gap-3 px-6 py-4 border-t border-brand-line hover:bg-brand-panel2 transition-colors text-left"
          >
            <span className="shrink-0 w-9 h-9 rounded-full bg-brand-blueSoft text-brand-blue font-bold text-sm flex items-center justify-center">
              {initials(me.sender_name)}
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-semibold text-brand-ink truncate">
                {me.sender_name || "Set your name"}
              </span>
              <span className="block text-xs text-brand-muted truncate">
                {me.resume_filename ? `📎 ${me.resume_filename}` : "No resume attached"}
              </span>
            </span>
          </button>
        </aside>

        {/* ── Main column ── */}
        <div className="flex-1 min-w-0 bg-brand-bg flex flex-col">
          {/* topbar */}
          <header className="sticky top-0 z-10 bg-brand-panel/95 backdrop-blur border-b border-brand-line">
            <div className="px-5 sm:px-8 py-4 flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-extrabold text-brand-ink tracking-tight">
                  {NAV.find((n) => n.id === tab)?.label}
                </h1>
                <p className="text-sm text-brand-muted mt-0.5">{SUBTITLES[tab]}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => api.downloadExportCsv().catch((e) => alert(e.message))}
                  className="text-sm font-semibold px-4 py-2 rounded-lg border border-brand-line2 text-brand-ink hover:bg-brand-panel2 transition-colors"
                >
                  Export CSV
                </button>
                <button
                  onClick={() => setTab("Add")}
                  className="bg-brand-blue text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-blueDark transition-colors"
                >
                  + New email
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
            {tab === "Add" && (
              <AddContact templates={templates} onAdded={refresh} settings={me} />
            )}
            {tab === "Board" && <Board refreshKey={refreshKey} goTo={setTab} />}
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
            {tab === "Settings" && <Settings />}
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
