export function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="sh-stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
