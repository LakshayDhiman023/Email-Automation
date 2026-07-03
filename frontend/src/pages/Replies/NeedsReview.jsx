import { useEffect, useState } from "react";
import { api } from "../../api";
import { useToast } from "../../components/Toast";
import { Button, Card, Empty, Input, Skeleton, fmt } from "../../components/ui";

const today = () => new Date().toISOString().slice(0, 10);

export default function NeedsReview({ refreshKey, onChange }) {
  const toast = useToast();
  const [threads, setThreads] = useState(null);
  const [replies, setReplies] = useState({}); // threadId -> latest reply snippet
  const [oooFor, setOooFor] = useState(null); // threadId whose OOO date-picker is open
  const [oooDate, setOooDate] = useState(today());

  async function load() {
    try {
      const list = await api.listThreads("replied_unlabeled");
      setThreads(list);
      const map = {};
      for (const t of list) {
        const r = await api.listReplies(t.id);
        map[t.id] = r[0];
      }
      setReplies(map);
    } catch {
      setThreads([]);
    }
  }
  useEffect(() => {
    load();
  }, [refreshKey]);

  async function label(threadId, lbl, returnDate) {
    try {
      await api.labelThread(threadId, { label: lbl, return_date: returnDate ?? null });
      toast(lbl === "out_of_office" ? "Follow-up rescheduled to return date" : `Labeled ${lbl}`, "success");
      setOooFor(null);
      await load();
      onChange?.();
    } catch (e) {
      toast(e.message, "error");
    }
  }

  if (threads === null) {
    return (
      <Card title="Needs review">
        <div className="space-y-3" aria-busy="true" aria-label="Loading replies to review">
          <Skeleton className="h-20 w-full rounded-xl" />
          <Skeleton className="h-20 w-full rounded-xl" />
        </div>
      </Card>
    );
  }

  return (
    <Card
      title={`Needs review (${threads.length})`}
      action={
        <Button
          variant="ghost"
          onClick={async () => {
            const { new_replies } = await api.pollReplies();
            toast(
              new_replies ? `${new_replies} new reply(ies) found` : "No new replies",
              new_replies ? "success" : "info"
            );
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
          <div key={t.id} className="rounded-xl border border-brand-line bg-brand-blueSoft p-4">
            <div className="flex items-center justify-between">
              <div className="font-medium text-brand-ink">
                {t.recruiter_name} · {t.company}
              </div>
              <div className="text-xs text-brand-muted">{t.email}</div>
            </div>
            {replies[t.id] && (
              <p className="mt-2 text-sm text-brand-muted italic">
                “{replies[t.id].snippet}”
                <span className="not-italic text-brand-muted">
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
              <Button
                variant="ghost"
                onClick={() => {
                  setOooDate(today());
                  setOooFor(oooFor === t.id ? null : t.id);
                }}
              >
                Out of office
              </Button>
              {oooFor === t.id && (
                <div className="flex items-end gap-2">
                  <div className="w-44">
                    <Input
                      label="Returns on"
                      type="date"
                      min={today()}
                      value={oooDate}
                      onChange={(e) => setOooDate(e.target.value)}
                    />
                  </div>
                  <Button
                    variant="primary"
                    disabled={!oooDate}
                    onClick={() => label(t.id, "out_of_office", oooDate)}
                  >
                    Reschedule
                  </Button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
