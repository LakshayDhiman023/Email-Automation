// Small themed UI primitives shared across sections.

export function Card({ title, action, children }) {
  return (
    <div className="rounded-2xl bg-white/80 backdrop-blur shadow-lg shadow-brand-deep/10 border border-white/60">
      {(title || action) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-brand-sky/30">
          <h2 className="font-semibold text-brand-ink">{title}</h2>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}

export function Button({ variant = "primary", className = "", ...props }) {
  const variants = {
    primary:
      "bg-brand-deep text-white hover:bg-brand-blue disabled:opacity-50",
    ghost:
      "bg-white/70 text-brand-ink hover:bg-white border border-brand-sky/50",
    danger: "bg-rose-500 text-white hover:bg-rose-600 disabled:opacity-50",
    success: "bg-emerald-500 text-white hover:bg-emerald-600",
  };
  return (
    <button
      className={`px-3.5 py-2 rounded-lg text-sm font-medium transition ${variants[variant]} ${className}`}
      {...props}
    />
  );
}

export function Input({ label, ...props }) {
  return (
    <label className="block">
      {label && (
        <span className="block text-sm font-medium text-brand-ink/80 mb-1">
          {label}
        </span>
      )}
      <input
        className="w-full rounded-lg border border-brand-sky/50 bg-white/90 px-3 py-2 text-sm outline-none focus:border-brand-deep focus:ring-2 focus:ring-brand-deep/20"
        {...props}
      />
    </label>
  );
}

export function Select({ label, children, ...props }) {
  return (
    <label className="block">
      {label && (
        <span className="block text-sm font-medium text-brand-ink/80 mb-1">
          {label}
        </span>
      )}
      <select
        className="w-full rounded-lg border border-brand-sky/50 bg-white/90 px-3 py-2 text-sm outline-none focus:border-brand-deep focus:ring-2 focus:ring-brand-deep/20"
        {...props}
      >
        {children}
      </select>
    </label>
  );
}

const STATUS_STYLES = {
  pending_approval: "bg-amber-100 text-amber-700",
  approved: "bg-sky-100 text-sky-700",
  sent: "bg-emerald-100 text-emerald-700",
  failed: "bg-rose-100 text-rose-700",
  cancelled: "bg-gray-200 text-gray-600",
  active: "bg-sky-100 text-sky-700",
  replied_unlabeled: "bg-violet-100 text-violet-700",
  replied_positive: "bg-emerald-100 text-emerald-700",
  replied_negative: "bg-rose-100 text-rose-700",
  ooo: "bg-amber-100 text-amber-700",
  dead: "bg-gray-200 text-gray-600",
};

export function Badge({ status }) {
  const cls = STATUS_STYLES[status] || "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

export function Empty({ children }) {
  return <p className="text-sm text-brand-ink/50 py-6 text-center">{children}</p>;
}

export function fmt(dt) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    dateStyle: "medium",
    timeStyle: "short",
  });
}
