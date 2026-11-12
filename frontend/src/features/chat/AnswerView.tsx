import { CircleCheck, CircleExclamationPoint, FileText, SearchX, Sparkles } from "lucide-react";
import type { Answer, Citation } from "../../api/types";
import { Feedback } from "../../components/ui/Feedback";
import { sourceLocation } from "../../lib/format";
export function AnswerView({
  answer,
  onSource,
}: {
  answer: Answer;
  onSource: (citation: Citation) => void;
}) {
  if (answer.source_unavailable)
    return (
      <Feedback title="Nguồn không còn khả dụng">
        Nội dung trả lời liên quan đã được ẩn vì nguồn bị xóa hoặc thay đổi.
      </Feedback>
    );
  const citations = answer.citations ?? [],
    claims = answer.claims ?? [];
  const valid =
    answer.answer_status === "insufficient_evidence" ||
    (claims.length > 0 &&
      claims.every(
        (c) =>
          c.evidence_ids.length > 0 &&
          c.evidence_ids.every((id) => citations.some((cite) => cite.evidence_id === id)),
      ));
  // Display numbers follow the backend citation order; evidence IDs stay the identity.
  const number = (id: string) => citations.findIndex((c) => c.evidence_id === id) + 1;
  const abstained = answer.answer_status === "insufficient_evidence";
  const partial = answer.answer_status === "partial";
  return (
    <article className={`answer ${abstained ? "answer-abstained" : ""}`}>
      <div className="answer-heading">
        <span className="answer-avatar" aria-hidden="true">
          <Sparkles size={16} />
        </span>
        <h3>Knowledge Copilot</h3>
        <span className="ai-label">AI-generated</span>
        {valid && !abstained && (
          <span className={`grounding grounding-${partial ? "partial" : "grounded"}`}>
            {partial ? (
              <CircleExclamationPoint size={13} aria-hidden="true" />
            ) : (
              <CircleCheck size={13} aria-hidden="true" />
            )}
            {partial ? "Trả lời một phần" : "Có nguồn dẫn"}
          </span>
        )}
      </div>
      {!valid ? (
        <Feedback title="Chưa thể hiển thị câu trả lời" kind="error">
          Thông tin nguồn chưa đầy đủ. Hãy tải lại lịch sử.
        </Feedback>
      ) : abstained ? (
        <div className="abstention" role="status">
          <SearchX size={20} aria-hidden="true" />
          <div>
            <h3>Chưa đủ bằng chứng trong tài liệu</h3>
            <p>
              {answer.reason_code === "no_ready_documents"
                ? "Chưa có tài liệu sẵn sàng. Hãy thêm tài liệu hoặc chờ quá trình xử lý hoàn tất."
                : "Chưa có thông tin đủ để trả lời câu hỏi này. Bạn có thể bổ sung tài liệu hoặc làm rõ câu hỏi."}
            </p>
          </div>
        </div>
      ) : (
        <>
          <div className="answer-claims">
            {claims.map((claim, i) => (
              <p key={i}>
                {claim.text}
                {claim.evidence_ids.map((id) => {
                  const cite = citations.find((c) => c.evidence_id === id)!;
                  return (
                    <button
                      key={id}
                      className="citation"
                      aria-label={`Mở nguồn ${id}`}
                      onClick={() => onSource(cite)}
                    >
                      {number(id)}
                      <span className="citation-preview" aria-hidden="true">
                        <strong>{cite.file_name}</strong>
                        <em>{sourceLocation(cite.location)}</em>
                        {cite.excerpt}
                      </span>
                    </button>
                  );
                })}
              </p>
            ))}
          </div>
          {(partial || answer.conflict_detected) && (
            <Feedback
              title={
                answer.conflict_detected
                  ? "Các nguồn có thông tin mâu thuẫn"
                  : "Một phần thông tin còn thiếu"
              }
              kind="warning"
            >
              {answer.limitations?.map((value, i) => (
                <p key={`l${i}`}>{value}</p>
              ))}
              {answer.missing_information?.map((value, i) => (
                <p key={`m${i}`}>{value}</p>
              ))}
            </Feedback>
          )}
          <div className="answer-sources">
            <h4>Nguồn tham chiếu · {citations.length}</h4>
            <div className="source-cards">
              {citations.map((c, i) => (
                <button className="source-card" key={c.evidence_id} onClick={() => onSource(c)}>
                  <span className="source-card-head">
                    <span className="source-number">{i + 1}</span>
                    <FileText size={14} aria-hidden="true" />
                    <span className="source-card-name">{c.file_name}</span>
                  </span>
                  <span className="source-card-location">{sourceLocation(c.location)}</span>
                  {c.excerpt && <span className="source-card-excerpt">{c.excerpt}</span>}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </article>
  );
}
