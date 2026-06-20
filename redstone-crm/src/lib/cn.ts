type ClassValue = string | number | null | boolean | undefined;

/**
 * Joins conditional class names together, skipping falsy values.
 * Usage: cn("px-2", isActive && "bg-red-50", error ? "text-red-600" : "text-slate-600")
 */
export function cn(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(" ");
}