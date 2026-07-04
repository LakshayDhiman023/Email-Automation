import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useToast } from "../components/Toast";
import { Button, Card, Input, Select } from "../components/ui";

const DAYS = [
  { n: 1, label: "Mon" },
  { n: 2, label: "Tue" },
  { n: 3, label: "Wed" },
  { n: 4, label: "Thu" },
  { n: 5, label: "Fri" },
  { n: 6, label: "Sat" },
  { n: 7, label: "Sun" },
];

// A small searchable timezone picker (Calendly/Google-style): type to filter,
// grouped by the current UTC offset so nearby zones are easy to find.
function TimezonePicker({ zones, value, onChange }) {
  const [q, setQ] = useState("");
  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const list = needle
      ? zones.filter((z) => z.toLowerCase().includes(needle))
      : zones;
    return list.slice(0, 200);
  }, [q, zones]);

  return (
    <div>
      <Input
        label="Timezone"
        placeholder="Search e.g. New York, London, Kolkata…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <Select
        className="mt-2"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        size={8}
      >
        {!filtered.includes(value) && <option value={value}>{value}</option>}
        {filtered.map((z) => (
          <option key={z} value={z}>
            {z.replace(/_/g, " ")}
          </option>
        ))}
      </Select>
      <p className="mt-1 text-xs text-brand-muted">
        Current selection: <b>{value.replace(/_/g, " ")}</b>
      </p>
    </div>
  );
}

function Window({ title, start, end, onStart, onEnd }) {
  return (
    <div className="rounded-xl border border-brand-line bg-brand-panel2 p-4">
      <div className="text-sm font-medium text-brand-ink mb-2">{title}</div>
      <div className="flex items-center gap-2">
        <input
          type="time"
          value={start}
          onChange={(e) => onStart(e.target.value)}
          className="rounded-lg border border-brand-line2 bg-white px-3 py-2 text-sm"
        />
        <span className="text-brand-muted">to</span>
        <input
          type="time"
          value={end}
          onChange={(e) => onEnd(e.target.value)}
          className="rounded-lg border border-brand-line2 bg-white px-3 py-2 text-sm"
        />
      </div>
    </div>
  );
}

export default function Settings({ goTo }) {
  const toast = useToast();
  const [zones, setZones] = useState([]);
  const [s, setS] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.listTimezones().then(setZones).catch(() => setZones([]));
    api
      .getSettings()
      .then((row) => setS({ ...row, working_days: row.working_days || [1, 2, 3, 4, 5] }))
      .catch((e) => toast(e.message, "error"));
  }, [toast]);

  if (!s) return <Card title="Settings">Loading… (run migration 003 if this stays empty)</Card>;

  const set = (k, v) => setS({ ...s, [k]: v });
  const toggleDay = (n) =>
    set(
      "working_days",
      s.working_days.includes(n)
        ? s.working_days.filter((d) => d !== n)
        : [...s.working_days, n].sort()
    );

  async function save() {
    setBusy(true);
    try {
      const saved = await api.updateSettings({
        timezone: s.timezone,
        window_a_start: s.window_a_start,
        window_a_end: s.window_a_end,
        window_b_start: s.window_b_start,
        window_b_end: s.window_b_end,
        working_days: s.working_days,
        followup_after_working_days: Number(s.followup_after_working_days),
        holiday_mode: s.holiday_mode,
        holiday_country: s.holiday_country || "IN",
        sender_name: s.sender_name || "",
        signature: s.signature || "",
      });
      setS({ ...saved });
      toast("Settings saved ✓", "success");
      goTo?.("Overview");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card title="Timezone & working days">
        <TimezonePicker zones={zones} value={s.timezone} onChange={(v) => set("timezone", v)} />

        <div className="mt-4">
          <span className="block text-sm font-medium text-brand-ink/80 mb-1.5">Working days</span>
          <div className="flex gap-1.5">
            {DAYS.map((d) => {
              const on = s.working_days.includes(d.n);
              return (
                <button
                  key={d.n}
                  onClick={() => toggleDay(d.n)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
                    on
                      ? "bg-brand-blue text-white border-brand-blue"
                      : "bg-white text-brand-muted border-brand-line2 hover:bg-brand-panel2"
                  }`}
                >
                  {d.label}
                </button>
              );
            })}
          </div>
          <p className="mt-1 text-xs text-brand-muted">Emails only send on selected days.</p>
        </div>
      </Card>

      <Card title="Send windows">
        <p className="text-sm text-brand-muted mb-3">
          Each email sends at a random time inside one of these two windows (human-looking).
        </p>
        <div className="grid gap-3">
          <Window
            title="Morning window"
            start={s.window_a_start}
            end={s.window_a_end}
            onStart={(v) => set("window_a_start", v)}
            onEnd={(v) => set("window_a_end", v)}
          />
          <Window
            title="Afternoon window"
            start={s.window_b_start}
            end={s.window_b_end}
            onStart={(v) => set("window_b_start", v)}
            onEnd={(v) => set("window_b_end", v)}
          />
        </div>
      </Card>

      <Card title="Follow-ups & holidays">
        <div className="grid gap-3">
          <Input
            label="Follow up after (working days with no reply)"
            type="number"
            min={1}
            max={30}
            value={s.followup_after_working_days}
            onChange={(e) => set("followup_after_working_days", e.target.value)}
          />
          <Select
            label="Skip public holidays"
            value={s.holiday_mode}
            onChange={(e) => set("holiday_mode", e.target.value)}
          >
            <option value="none">No — send on any working day</option>
            <option value="country">Yes — skip my country's public holidays</option>
          </Select>
          {s.holiday_mode === "country" && (
            <Input
              label="Country code (ISO, e.g. IN, US, GB)"
              value={s.holiday_country}
              onChange={(e) => set("holiday_country", e.target.value.toUpperCase())}
            />
          )}
        </div>
      </Card>

      <Card title="Your identity">
        <div className="grid gap-3">
          <Input
            label="Your name"
            placeholder="e.g. Jordan Lee"
            value={s.sender_name || ""}
            onChange={(e) => set("sender_name", e.target.value)}
          />
          <label className="block">
            <span className="block text-sm font-medium text-brand-ink/80 mb-1.5">
              Email signature (use {"{signature}"} in a template to insert this)
            </span>
            <textarea
              rows={4}
              className="w-full rounded-lg border border-brand-line2 bg-white px-3.5 py-2.5 text-sm text-brand-ink outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/15 transition"
              placeholder={"Best regards,\nJordan Lee\n+1 555 0100"}
              value={s.signature || ""}
              onChange={(e) => set("signature", e.target.value)}
            />
          </label>
        </div>
      </Card>

      <Card title="">
        <Button onClick={save} disabled={busy}>
          {busy ? "Saving…" : "Save settings"}
        </Button>
        <p className="mt-2 text-xs text-brand-muted">
          Changes apply to newly scheduled emails immediately.
        </p>
      </Card>
    </div>
  );
}
