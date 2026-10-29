type Props = { title: string; description: string };

/** Trang giữ chỗ; thay bằng trang thật khi triển khai từng màn hình. */
export default function PlaceholderPage({ title, description }: Props) {
  return (
    <section>
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="mt-1 text-slate-600">{description}</p>
      <p className="mt-4 inline-block rounded bg-amber-100 px-2 py-1 text-sm text-amber-800">
        Chưa triển khai
      </p>
    </section>
  );
}
