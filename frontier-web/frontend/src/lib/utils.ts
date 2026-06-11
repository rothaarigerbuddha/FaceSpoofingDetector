import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


export function generateSlug(title: string) {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}


export function getImageUrlFromPath(path: string | null) {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5160";
  return path ? `${baseUrl}/images/posts/${path}` : "https://images.unsplash.com/photo-1511285605577-4d62fb50d2f7?fm=jpg&q=60&w=3000&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MjB8fHBsYWNlaG9sZGVyfGVufDB8fDB8fHww";
}

export function formatDate(utcString: string): string {
  const date = new Date(utcString);
 
  if (isNaN(date.getTime())) return 'Invalid date';
 
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}
 