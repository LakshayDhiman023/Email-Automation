import { useState } from "react";
import { SubTabs } from "../../components/ui";
import NeedsReview from "./NeedsReview";
import ThreadList from "./ThreadList";

// Reply-handling views (needs-review / positive / dead) behind one nav entry.
export default function Replies({ refreshKey, onChange, stats }) {
  const [sub, setSub] = useState("Needs review");
  return (
    <div>
      <SubTabs
        tabs={["Needs review", "Positive", "Dead"]}
        active={sub}
        onChange={setSub}
        counts={{
          "Needs review": stats.needs_review,
          Positive: stats.positive,
          Dead: stats.negative,
        }}
      />
      {sub === "Needs review" && <NeedsReview refreshKey={refreshKey} onChange={onChange} />}
      {sub === "Positive" && (
        <ThreadList
          title="Attention — positive replies"
          status="replied_positive"
          refreshKey={refreshKey}
        />
      )}
      {sub === "Dead" && (
        <ThreadList title="Dead threads" status="replied_negative" refreshKey={refreshKey} />
      )}
    </div>
  );
}
