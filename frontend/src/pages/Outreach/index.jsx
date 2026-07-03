import { useState } from "react";
import { SubTabs } from "../../components/ui";
import Approvals from "./Approvals";
import SendList from "./SendList";

// Send-lifecycle views (approvals / scheduled / sent) behind one nav entry.
export default function Outreach({ refreshKey, onChange, stats }) {
  const [sub, setSub] = useState("Approvals");
  return (
    <div>
      <SubTabs
        tabs={["Approvals", "Scheduled", "Sent"]}
        active={sub}
        onChange={setSub}
        counts={{ Approvals: stats.pending_approval, Scheduled: stats.scheduled }}
      />
      {sub === "Approvals" && <Approvals refreshKey={refreshKey} onChange={onChange} />}
      {sub === "Scheduled" && (
        <SendList
          title="Scheduled queue"
          status="approved"
          refreshKey={refreshKey}
          emptyText="Nothing scheduled yet — approved emails will queue up here."
        />
      )}
      {sub === "Sent" && (
        <SendList
          title="Sent log"
          status="sent"
          refreshKey={refreshKey}
          timeField="sent_at"
          emptyText="Nothing sent yet — your sent emails will show up here."
        />
      )}
    </div>
  );
}
