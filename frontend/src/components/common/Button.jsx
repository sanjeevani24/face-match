import { Loader2 } from "lucide-react";

const VARIANTS = {
  primary: "bg-[var(--color-brand-blue)] text-white hover:bg-[var(--color-brand-blue-dark)] disabled:opacity-50",
  success: "bg-[var(--color-brand-green)] text-white hover:bg-[var(--color-brand-green-dark)] disabled:opacity-50",
  outline:
    "bg-white text-[var(--color-brand-blue)] border border-[var(--color-border)] hover:border-[var(--color-brand-blue)] disabled:opacity-50",
  ghost: "bg-transparent text-[var(--color-ink-soft)] hover:bg-black/5 disabled:opacity-50",
  danger: "bg-[var(--color-danger)] text-white hover:opacity-90 disabled:opacity-50",
};

export default function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  icon: Icon,
  className = "",
  disabled,
  ...props
}) {
  const sizes = {
    sm: "text-sm px-3 py-1.5 gap-1.5",
    md: "text-sm px-4 py-2.5 gap-2",
    lg: "text-base px-6 py-3 gap-2",
  };

  return (
    <button
      className={`inline-flex items-center justify-center rounded-xl font-medium transition-colors duration-150 disabled:cursor-not-allowed ${VARIANTS[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="size-4 animate-spin" /> : Icon ? <Icon className="size-4" /> : null}
      {children}
    </button>
  );
}
