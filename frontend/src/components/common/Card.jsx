export default function Card({ title, subtitle, action, children, className = "", padded = true }) {
  return (
    <div className={`card ${className}`}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-4 border-b border-[var(--color-border)] px-6 py-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-[var(--color-ink)]">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-[var(--color-ink-faint)]">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className={padded ? "p-6" : ""}>{children}</div>
    </div>
  );
}
