import { useEffect, useState } from "react";
import { api } from "../api";
import { Card } from "../components/ui";

// Onboarding steps in completion order; `tab` is where the unfinished step is done.
const SETUP_STEPS = [
  { key: "gmail_connected", label: "Connect Gmail", hint: "configure in backend/.env" },
  { key: "identity_set", label: "Set your name & signature", tab: "Settings", cta: "Go to Settings →" },
  { key: "template_created", label: "Create your first template", tab: "Templates", cta: "Go to Templates →" },
  { key: "first_send_sent", label: "Queue & approve your first email", tab: "Add", cta: "New email →" },
];

// Progress card shown until every setup step is really done, then it vanishes.
function SetupChecklist({ setup, goTo }) {
  if (!setup || setup.complete) return null;
  const done = SETUP_STEPS.filter((s) => setup[s.key]).length;
  return (
    <div className="md:col-span-2 rounded-2xl border border-blue-200 bg-gradient-to-b from-brand-blueSoft to-brand-panel p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-extrabold text-brand-ink">Finish setting up Mailflow</span>
        <span className="text-xs font-bold text-brand-blue">
          {done} of {SETUP_STEPS.length} done
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-brand-line overflow-hidden mb-4">
        <div
          className="h-full bg-brand-blue rounded-full transition-all"
          style={{ width: `${(done / SETUP_STEPS.length) * 100}%` }}
        />
      </div>
      <div className="grid gap-2">
        {SETUP_STEPS.map((s) => {
          const ok = setup[s.key];
          return (
            <div key={s.key} className="flex items-center gap-2.5 text-sm">
              {ok ? (
                <span className="w-[18px] h-[18px] rounded-full bg-emerald-50 text-emerald-600 text-[11px] font-extrabold inline-flex items-center justify-center">
                  ✓
                </span>
              ) : (
                <span className="w-[18px] h-[18px] rounded-full border-[1.5px] border-brand-line2 inline-flex" />
              )}
              <span
                className={
                  ok ? "text-brand-muted line-through" : "font-semibold text-brand-ink flex-1"
                }
              >
                {s.label}
              </span>
              {!ok &&
                (s.tab ? (
                  <button
                    onClick={() => goTo(s.tab)}
                    className="text-xs font-bold text-brand-blue hover:text-brand-blueDark"
                  >
                    {s.cta}
                  </button>
                ) : (
                  <span className="text-xs text-brand-muted">{s.hint}</span>
                ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

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
  const [setup, setSetup] = useState(null);

  useEffect(() => {
    api.stats().then(setS).catch(() => setS(null));
    api.setupStatus().then(setSetup).catch(() => setSetup(null));
  }, [refreshKey]);

  if (!s) return null;

  const needsAttention = s.needs_review > 0 || s.pending_approval > 0;

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <SetupChecklist setup={setup} goTo={goTo} />
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
