import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  loading?: boolean;
  icon?: ReactNode;
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = "secondary", loading = false, icon, children, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      {...props}
      className={`button button-${variant} ${props.className ?? ""}`}
      disabled={loading || props.disabled}
      aria-busy={loading}
    >
      {loading ? <span className="spinner" aria-hidden="true" /> : icon}
      <span>{children}</span>
    </button>
  );
});
