import { useEffect, useState } from "react";
import { api } from "../../api";
import { Badge, Card, Empty, fmt } from "../../components/ui";

// Reused for both the Scheduled Queue (status=approved) and Sent Log (status=sent).
export default function SendList({ title, status, refreshKey, timeField = "scheduled_at" }) {
  const [sends, setSends] = useState([]);

  useEffect(() => {
    api.listSends(status).then(setSends);
  }, [status, refreshKey]);

  return (
    <Card title={`${title} (${sends.length})`}>
      {sends.length === 0 && <Empty>Nothing here yet.</Empty>}
      <div className="space-y-2">
        {sends.map((s) => (
          <div
            key={s.id}
            className="flex items-center justify-between rounded-lg border border-brand-line bg-brand-panel2 hover:bg-brand-blueSoft transition px-4 py-2.5"
          >
            <div className="min-w-0">
              <div className="truncate font-medium text-brand-ink">{s.subject}</div>
              <div className="text-xs text-brand-muted">
                {s.type} · {fmt(s[timeField])}
              </div>
            </div>
            <Badge status={s.status} />
          </div>
        ))}
      </div>
    </Card>
  );
}
