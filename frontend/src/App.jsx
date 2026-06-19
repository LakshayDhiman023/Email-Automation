import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import AddContact from "./sections/AddContact";
import Approvals from "./sections/Approvals";
import NeedsReview from "./sections/NeedsReview";
import SendList from "./sections/SendList";
import Templates from "./sections/Templates";
import ThreadList from "./sections/ThreadList";

const TABS = [
  "Add",
  "Approvals",
  "Scheduled",
  "Sent",
  "Needs review",
  "Attention",
  "Dead",
  "Templates",
];

export default function App() {
  const [tab, setTab] = useState("Add");
  const [templates, setTemplates] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);
  const loadTemplates = useCallback(() => {
    api.listTemplates().then(setTemplates).catch(() => setTemplates([]));
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates, refreshKey]);

  return (
    <div className="min-h-full bg-brand-wash">
      <header className="bg-gradient-to-r from-brand-sky via-brand-blue to-brand-violet">
        <div className="max-w-5xl mx-auto px-6 py-6 flex items-end justify-between">
          <div>
            <div className="text-xs tracking-[0.3em] text-white/80 font-semibold leading-5">
              BUILD · THINK · INNOVATE
            </div>
            <h1 className="text-2xl font-bold text-white drop-shadow-sm">
              Recruiter Outreach
            </h1>
          </div>
          <div className="text-right text-white/90 text-sm">
            <div className="font-semibold">Ved Prakash Meena</div>
            <div className="text-white/70">connect.ved21@gmail.com</div>
          </div>
        </div>
      </header>

      <nav className="sticky top-0 z-10 bg-white/70 backdrop-blur border-b border-white/60">
        <div className="max-w-5xl mx-auto px-6 flex gap-1 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition ${
                tab === t
                  ? "border-brand-deep text-brand-deep"
                  : "border-transparent text-brand-ink/60 hover:text-brand-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {tab === "Add" && <AddContact templates={templates} onAdded={refresh} />}
        {tab === "Approvals" && <Approvals refreshKey={refreshKey} onChange={refresh} />}
        {tab === "Scheduled" && (
          <SendList title="Scheduled queue" status="approved" refreshKey={refreshKey} />
        )}
        {tab === "Sent" && (
          <SendList
            title="Sent log"
            status="sent"
            refreshKey={refreshKey}
            timeField="sent_at"
          />
        )}
        {tab === "Needs review" && (
          <NeedsReview refreshKey={refreshKey} onChange={refresh} />
        )}
        {tab === "Attention" && (
          <ThreadList
            title="Attention — positive replies"
            status="replied_positive"
            refreshKey={refreshKey}
          />
        )}
        {tab === "Dead" && (
          <ThreadList
            title="Dead threads"
            status="replied_negative"
            refreshKey={refreshKey}
          />
        )}
        {tab === "Templates" && (
          <Templates templates={templates} onChange={loadTemplates} />
        )}
      </main>
    </div>
  );
}
