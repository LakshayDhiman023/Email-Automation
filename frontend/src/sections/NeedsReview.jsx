import { useEffect, useState } from "react";
import { api } from "../api";
import { Button, Card, Empty, Input, fmt } from "../components/ui";

export default function NeedsReview({ refreshKey, onChange }) {
  const [threads, setThreads] = useState([]);
  const [replies, setReplies] = useState({}); // threadId -> latest reply snippet
  const [oooDate, setOooDate] = useState({}); // threadId -> date string

  async function load() {
    const list = await api.listThreads("replied_unlabeled");
    setThreads(list);
    const map = {};
    for (const t of list) {
      const r = await api.listReplies(t.id);
      map[t.id] = r[0];
    }
    setReplies(map);
  }
  useEffect(() => {
    load();
  }, [refreshKey]);

  async function label(threadId, lbl) {
    const payload = { label: lbl };
    if (lbl === "ooo") {
      if (!oooDate[threadId]) return alert("Enter the recruiter's return date first.");
      payload.ooo_return_date = oooDate[threadId];
    }
    await api.labelThread(threadId, payload);
    await load();
    onChange?.();
  }

  return (
    <Card
      title={`Needs review (${threads.length})`}
      action={
        <Button
          variant="ghost"
          onClick={async () => {
            await api.pollReplies();
            await load();
            onChange?.();
          }}
        >
          Check for replies
        </Button>
      }
    >
      {threads.length === 0 && <Empty>No replies waiting to be labeled.</Empty>}
      <div className="space-y-3">
        {threads.map((t) => (
          <div key={t.id} className="rounded-xl border border-violet-200 bg-violet-50/60 p-4">
            <div className="flex items-center justify-between">
              <div className="font-medium text-brand-ink">
                {t.recruiter_name} · {t.company}
              </div>
              <div className="text-xs text-brand-ink/60">{t.email}</div>
            </div>
            {replies[t.id] && (
              <p className="mt-2 text-sm text-brand-ink/75 italic">
                “{replies[t.id].snippet}”
                <span className="not-italic text-brand-ink/50">
                  {" "}
                  · {fmt(replies[t.id].received_at)}
                </span>
              </p>
            )}
            <div className="mt-3 flex flex-wrap items-end gap-2">
              <Button variant="success" onClick={() => label(t.id, "positive")}>
                Positive
              </Button>
              <Button variant="danger" onClick={() => label(t.id, "negative")}>
                Negative
              </Button>
              <div className="flex items-end gap-2">
                <div className="w-40">
                  <Input
                    label="OOO return date"
                    type="date"
                    value={oooDate[t.id] || ""}
                    onChange={(e) => setOooDate({ ...oooDate, [t.id]: e.target.value })}
                  />
                </div>
                <Button variant="ghost" onClick={() => label(t.id, "ooo")}>
                  Mark OOO
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
