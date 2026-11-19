import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api";
import { isAbort } from "../../api/client";
import type { Job, KnowledgeDocument } from "../../api/types";
export function useDocuments(folderId?: string) {
  const [items, setItems] = useState<KnowledgeDocument[]>([]),
    [jobs, setJobs] = useState<Record<string, Job>>({});
  const [error, setError] = useState<unknown>(null),
    [loading, setLoading] = useState(true),
    [jobError, setJobError] = useState(false);
  const [paused, setPaused] = useState(false),
    [epoch, setEpoch] = useState(0);
  const controller = useRef<AbortController | null>(null);
  const load = useCallback(async () => {
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    try {
      const docs = await api.documents(next.signal, folderId);
      const results = await Promise.allSettled(
        docs.items
          .filter((d) => d.latest_job_id)
          .map((d) => api.job(d.latest_job_id!, next.signal)),
      );
      if (next.signal.aborted) return;
      setItems(docs.items);
      setJobs(
        Object.fromEntries(
          results.flatMap((r) => (r.status === "fulfilled" ? [[r.value.id, r.value]] : [])),
        ),
      );
      setJobError(results.some((r) => r.status === "rejected"));
      setError(null);
    } catch (e) {
      if (!isAbort(e)) setError(e);
    } finally {
      if (!next.signal.aborted) setLoading(false);
    }
  }, [folderId]);
  useEffect(() => {
    setLoading(true);
    void load();
    // "focus" and "visibilitychange" both fire on tab return; load once, in the background.
    let timer: ReturnType<typeof setTimeout> | undefined;
    const focus = () => {
      if (document.hidden) return;
      clearTimeout(timer);
      timer = setTimeout(() => void load(), 150);
    };
    window.addEventListener("focus", focus);
    document.addEventListener("visibilitychange", focus);
    return () => {
      clearTimeout(timer);
      controller.current?.abort();
      window.removeEventListener("focus", focus);
      document.removeEventListener("visibilitychange", focus);
    };
  }, [load]);
  const active = items.some(
    (d) =>
      ["queued", "processing", "deleting"].includes(d.status) &&
      (!d.latest_job_id ||
        !jobs[d.latest_job_id] ||
        !["completed", "failed", "cancelled"].includes(jobs[d.latest_job_id].status)),
  );
  useEffect(() => {
    if (!active) return;
    let stopped = false,
      timer: ReturnType<typeof setTimeout>;
    const started = Date.now();
    let delay = 2000;
    const tick = async () => {
      if (stopped) return;
      if (Date.now() - started >= 15 * 60 * 1000) {
        setPaused(true);
        return;
      }
      if (!document.hidden) await load();
      if (!stopped) {
        delay = Math.min(10000, delay * 1.5);
        timer = setTimeout(() => void tick(), delay);
      }
    };
    timer = setTimeout(() => void tick(), delay);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [active, epoch, load]);
  const refresh = useCallback(() => {
    setPaused(false);
    setEpoch((e) => e + 1);
    void load();
  }, [load]);
  return { items, jobs, error, loading, jobError, paused, refresh };
}
