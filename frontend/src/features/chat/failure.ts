/** Plain-language copy for answering failures. These are technical errors, never "no evidence". */
const COPY: Record<string, { title: string; body: string }> = {
  model_timeout: {
    title: "Gemini không phản hồi kịp",
    body: "Gemini không trả lời kịp, thường do đang quá tải. Câu hỏi chưa được trả lời; bạn có thể hỏi lại sau ít phút.",
  },
  model_unavailable: {
    title: "Chưa kết nối được model",
    body: "Dịch vụ sinh câu trả lời đang tắt hoặc tạm thời không khả dụng. Câu hỏi chưa được trả lời.",
  },
  model_busy: {
    title: "Model đang bận",
    body: "Hệ thống đang xử lý câu hỏi khác. Vui lòng hỏi lại sau ít giây.",
  },
  invalid_model_output: {
    title: "Câu trả lời của model không hợp lệ",
    body: "Model trả về nội dung sai định dạng hoặc trích dẫn sai, nên hệ thống không hiển thị. Bạn có thể hỏi lại.",
  },
  retrieval_unavailable: {
    title: "Chưa tìm được trong kho tài liệu",
    body: "Dịch vụ tìm kiếm tạm thời lỗi. Câu hỏi chưa được trả lời.",
  },
  source_changed: {
    title: "Tài liệu nguồn vừa thay đổi",
    body: "Một tài liệu được dùng để trả lời đã bị xóa hoặc thay đổi trong lúc xử lý. Hãy hỏi lại.",
  },
};
/** model_unavailable carries details.reason from the backend adapter (HTTP status class). */
const PROVIDER_REASONS: Record<string, { title: string; body: string }> = {
  quota: {
    title: "Đã hết quota Gemini free tier",
    body: "Đã chạm giới hạn số lần gọi của gói miễn phí. Quota theo ngày được làm mới khoảng 15:00 giờ Việt Nam; giới hạn theo phút hết sau ít phút.",
  },
  overloaded: {
    title: "Gemini đang quá tải",
    body: "Dịch vụ của Google tạm thời lỗi hoặc quá tải. Câu hỏi chưa được trả lời; bạn có thể hỏi lại sau ít phút.",
  },
  rejected: {
    title: "Gemini từ chối yêu cầu",
    body: "Có thể API key hoặc cấu hình model chưa đúng. Hãy báo quản trị viên kiểm tra.",
  },
  network: {
    title: "Không kết nối được tới Gemini",
    body: "Máy chủ không truy cập được dịch vụ của Google. Kiểm tra kết nối mạng rồi hỏi lại.",
  },
};
export function failureCopy(code?: string | null, reason?: unknown) {
  if (code === "model_unavailable" && typeof reason === "string" && PROVIDER_REASONS[reason])
    return PROVIDER_REASONS[reason];
  return code ? (COPY[code] ?? null) : null;
}
/** Server-side query deadline (QUERY_TIMEOUT_SECONDS); shown so a long wait has a known end. */
export const QUERY_DEADLINE_SECONDS = 150;
export const SLOW_AFTER_SECONDS = 60;
