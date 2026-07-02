import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { fmt } from "../components/ui";

// Kanban pipeline of every thread, bucketed by where it stands in the send
// lifecycle. Read-only by design (P3: state changes happen through the explicit
// approve/label flows) — each card links to the tab where the action lives.

const COLUMNS = [
  { id: "pending", title: "Pending approval", tab: "Outreach", accent: "bg-amber-400" },
  { id: "scheduled", title: "Scheduled", tab: "Outreach", accent: "bg-brand-blue" },
  { id: "awaiting", title: "Awaiting reply", tab: "Outreach", accent: "bg-sky-400" },
  { id: "replied", title: "Replied", tab: "Replies", accent: "bg-emerald-500" },
  { id: "closed", title: "Closed", tab: "Replies", accent: "bg-neutral-300" },
];

const REPLIED = new Set(["replied_unlabeled", "replied_positive", "replied_negative", "ooo"]);

function bucket(t) {
  if (REPLIED.has(t.status)) return "replied";
  if (t.status !== "active") return "closed"; // dead / bounced
  switch (t.latest_send?.status) {
    case "pending_approval":
      return "pending";
    case "approved":
    case "sending":
      return "scheduled";
    case "sent":
    case "failed": // failed shows here with its error so it isn't lost
      return "awaiting";
    default:
      return "closed"; // cancelled or no send left
  }
}

const CHIP = {
  replied_positive: ["Positive", "bg-emerald-50 text-emerald-700"],
  replied_negative: ["Negative", "bg-red-50 text-red-700"],
  replied_unlabeled: ["Needs review", "bg-amber-50 text-amber-700"],
  ooo: ["Out of office", "bg-sky-50 text-sky-700"],
  bounced: ["Bounced", "bg-red-50 text-red-700"],
  dead: ["Closed", "bg-neutral-100 text-neutral-500"],
  failed: ["Send failed", "bg-red-50 text-red-700"],
};

function Chip({ kind }) {
  const c = CHIP[kind];
  if (!c) return null;
  return (
    <span className={`text-[10px] font-bold rounded-full px-2 py-0.5 ${c[1]}`}>{c[0]}</span>
  );
}

export default function Board({ refreshKey, goTo }) {
  const [threads, setThreads] = useState(null);

  useEffect(() => {
    api.listThreads().then(setThreads).catch(() => setThreads([]));
  }, [refreshKey]);

  const lanes = useMemo(() => {
    const by = Object.fromEntries(COLUMNS.map((c) => [c.id, []]));
    for (const t of threads || []) by[bucket(t)].push(t);
    return by;
  }, [threads]);

  if (threads === null) {
    return <div className="text-sm text-brand-muted py-10 text-center">Loading pipeline…</div>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5 items-start">
      {COLUMNS.map((col) => (
        <div key={col.id} className="rounded-2xl bg-brand-panel2/60 border border-brand-line">
          <div className="flex items-center gap-2 px-4 py-3">
            <span className={`w-2 h-2 rounded-full ${col.accent}`} />
            <span className="text-sm font-bold text-brand-ink flex-1">{col.title}</span>
            <span className="text-xs font-semibold text-brand-muted">{lanes[col.id].length}</span>
          </div>
          <div className="px-3 pb-3 space-y-2">
            {lanes[col.id].length === 0 && (
              <div className="text-xs text-brand-muted text-center py-6">Nothing here</div>
            )}
            {lanes[col.id].map((t) => {
              const ls = t.latest_send;
              const chipKind = REPLIED.has(t.status) || t.status !== "active"
                ? t.status
                : ls?.status === "failed"
                ? "failed"
                : null;
              return (
                <button
                  key={t.id}
                  onClick={() => goTo(col.tab)}
                  className="w-full text-left rounded-xl bg-brand-panel border border-brand-line p-3 hover:border-brand-blue/40 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-semibold text-brand-ink truncate">
                      {t.company}
                    </span>
                    {chipKind && <Chip kind={chipKind} />}
                  </div>
                  <div className="text-xs text-brand-muted truncate">
                    {t.recruiter_name !== "there" ? `${t.recruiter_name} · ` : ""}
                    {t.email}
                  </div>
                  {ls && (
                    <div className="mt-2 text-xs text-brand-muted truncate" title={ls.subject}>
                      {ls.type === "followup" ? "↩ " : ""}
                      {ls.subject}
                    </div>
                  )}
                  <div className="mt-1 text-[11px] text-brand-muted/80">
                    {ls?.sent_at
                      ? `Sent ${fmt(ls.sent_at)}`
                      : ls?.scheduled_at
                      ? `Scheduled ${fmt(ls.scheduled_at)}`
                      : fmt(t.created_at)}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
