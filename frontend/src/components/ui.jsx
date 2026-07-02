// UI primitives — light, clean, recruitment-blue (Naukri-referenced ~50%).

export function Card({ title, action, children }) {
  return (
    <div className="bg-brand-panel rounded-xl shadow-card border border-brand-line overflow-hidden">
      {(title || action) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-brand-line">
          <h2 className="font-semibold text-brand-ink">{title}</h2>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}

export function Button({ variant = "primary", className = "", ...props }) {
  const base =
    "px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 active:scale-[0.98]";
  const variants = {
    primary: "text-white bg-brand-blue hover:bg-brand-blueDark shadow-blue disabled:opacity-40",
    ghost: "text-brand-blue bg-brand-blueSoft hover:bg-brand-blue/15 border border-brand-blue/20",
    danger: "text-rose-600 bg-rose-50 border border-rose-200 hover:bg-rose-100",
    success: "text-white bg-brand-teal hover:brightness-95",
  };
  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />;
}

export function Input({ label, ...props }) {
  return (
    <label className="block">
      {label && (
        <span className="block text-sm font-medium text-brand-ink/80 mb-1.5">{label}</span>
      )}
      <input
        className="w-full rounded-lg border border-brand-line2 bg-white px-3.5 py-2.5 text-sm text-brand-ink placeholder-brand-muted/60 outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/15 transition"
        {...props}
      />
    </label>
  );
}

export function Select({ label, children, className = "", ...props }) {
  return (
    <label className="block">
      {label && (
        <span className="block text-sm font-medium text-brand-ink/80 mb-1.5">{label}</span>
      )}
      <select
        className={`w-full rounded-lg border border-brand-line2 bg-white px-3.5 py-2.5 text-sm text-brand-ink outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/15 transition ${className}`}
        {...props}
      >
        {children}
      </select>
    </label>
  );
}

const STATUS_STYLES = {
  pending_approval: "bg-amber-50 text-amber-700 border-amber-200",
  approved: "bg-brand-blueSoft text-brand-blue border-brand-blue/20",
  sent: "bg-emerald-50 text-emerald-700 border-emerald-200",
  failed: "bg-rose-50 text-rose-700 border-rose-200",
  cancelled: "bg-gray-100 text-gray-500 border-gray-200",
  active: "bg-brand-blueSoft text-brand-blue border-brand-blue/20",
  replied_unlabeled: "bg-indigo-50 text-indigo-700 border-indigo-200",
  replied_positive: "bg-emerald-50 text-emerald-700 border-emerald-200",
  replied_negative: "bg-rose-50 text-rose-700 border-rose-200",
  ooo: "bg-amber-50 text-amber-700 border-amber-200",
  bounced: "bg-orange-50 text-orange-700 border-orange-200",
  dead: "bg-gray-100 text-gray-500 border-gray-200",
};

export function Badge({ status }) {
  const cls = STATUS_STYLES[status] || "bg-gray-100 text-gray-600 border-gray-200";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cls}`}>
      {status}
    </span>
  );
}

export function Empty({ children }) {
  return <p className="text-sm text-brand-muted py-10 text-center">{children}</p>;
}

// Pill-style secondary toggle used inside grouped pages.
export function SubTabs({ tabs, active, onChange, counts = {} }) {
  return (
    <div className="inline-flex gap-1 p-1 rounded-lg bg-white border border-brand-line mb-5 shadow-card">
      {tabs.map((t) => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
            active === t
              ? "bg-brand-blue text-white"
              : "text-brand-muted hover:text-brand-ink hover:bg-brand-panel2"
          }`}
        >
          {t}
          {counts[t] > 0 && (
            <span
              className={`text-[10px] font-bold rounded-full min-w-[16px] h-4 px-1 inline-flex items-center justify-center ${
                active === t ? "bg-white/25" : "bg-brand-blueSoft text-brand-blue"
              }`}
            >
              {counts[t]}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

export function fmt(dt) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    dateStyle: "medium",
    timeStyle: "short",
  });
}
