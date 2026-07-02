import { useEffect, useState } from "react";
import { api } from "../api";
import { Card } from "../components/ui";

function Row({ label, value, accent, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border border-brand-line bg-brand-panel2 transition ${
        onClick ? "hover:bg-brand-blueSoft cursor-pointer" : "cursor-default"
      }`}
    >
      <span className="text-sm text-brand-muted">{label}</span>
      <span className={`text-lg font-bold ${accent || "text-brand-ink"}`}>{value}</span>
    </button>
  );
}

export default function Overview({ refreshKey, goTo }) {
  const [s, setS] = useState(null);

  useEffect(() => {
    api.stats().then(setS).catch(() => setS(null));
  }, [refreshKey]);

  if (!s) return null;

  const needsAttention = s.needs_review > 0 || s.pending_approval > 0;

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Card title="Needs your action">
        <div className="space-y-2">
          <Row
            label="Drafts awaiting approval"
            value={s.pending_approval}
            accent={s.pending_approval ? "text-amber-600" : "text-brand-muted"}
            onClick={() => goTo("Outreach")}
          />
          <Row
            label="Replies to review"
            value={s.needs_review}
            accent={s.needs_review ? "text-brand-blue" : "text-brand-muted"}
            onClick={() => goTo("Replies")}
          />
          {!needsAttention && (
            <p className="text-sm text-brand-muted pt-2 text-center">
              All caught up — nothing needs you right now.
            </p>
          )}
        </div>
      </Card>

      <Card title="Pipeline">
        <div className="space-y-2">
          <Row label="Scheduled to send" value={s.scheduled} accent="text-brand-blue" onClick={() => goTo("Outreach")} />
          <Row label="Awaiting reply" value={s.active} accent="text-brand-blue" />
          <Row label="Sent total" value={s.sent} accent="text-emerald-600" onClick={() => goTo("Outreach")} />
          <Row label="Reply rate" value={`${s.reply_rate}%`} />
        </div>
      </Card>

      <Card title="Outcomes">
        <div className="grid grid-cols-3 gap-2">
          <Row label="Positive" value={s.positive} accent="text-emerald-600" onClick={() => goTo("Replies")} />
          <Row label="Negative" value={s.negative} accent="text-rose-600" onClick={() => goTo("Replies")} />
          <Row label="Out of office" value={s.ooo ?? 0} accent="text-amber-600" onClick={() => goTo("Replies")} />
        </div>
      </Card>
    </div>
  );
}
