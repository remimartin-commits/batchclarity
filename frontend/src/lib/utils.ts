import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Required by shadcn/ui — merges Tailwind classes without conflicts
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
