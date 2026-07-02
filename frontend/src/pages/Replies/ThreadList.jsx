import { useEffect, useState } from "react";
import { api } from "../../api";
import { Badge, Card, Empty, fmt } from "../../components/ui";

// Reused for Attention (replied_positive), Dead (replied_negative), OOO, etc.
export default function ThreadList({ title, status, refreshKey }) {
  const [threads, setThreads] = useState([]);

  useEffect(() => {
    api.listThreads(status).then(setThreads);
  }, [status, refreshKey]);

  return (
    <Card title={`${title} (${threads.length})`}>
      {threads.length === 0 && <Empty>None.</Empty>}
      <div className="space-y-2">
        {threads.map((t) => (
          <div
            key={t.id}
            className="flex items-center justify-between rounded-lg border border-brand-line bg-brand-panel2 hover:bg-brand-blueSoft transition px-4 py-2.5"
          >
            <div>
              <div className="font-medium text-brand-ink">
                {t.recruiter_name} · {t.company}
              </div>
              <div className="text-xs text-brand-muted">
                {t.email}
                {t.ooo_return_date ? ` · back ${fmt(t.ooo_return_date)}` : ""}
              </div>
            </div>
            <Badge status={t.status} />
          </div>
        ))}
      </div>
    </Card>
  );
}
