export type IconName = "pin" | "radius" | "areas" | "search" | "lock" | "check" | "arrow" | "info";

export default function Icon({ name }: { name: IconName }) {
  const paths = {
    pin: <><path d="M12 21s-6-5.2-6-11a6 6 0 0 1 12 0c0 5.8-6 11-6 11Z" /><circle cx="12" cy="10" r="2" /></>,
    radius: <><circle cx="12" cy="12" r="9" strokeDasharray="2.5 3" /><circle cx="12" cy="12" r="3" fill="currentColor" stroke="none" /></>,
    areas: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Zm6-3v15m6-12v15" /></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 5 5" /></>,
    lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    arrow: <><path d="M4 12h16m-6-6 6 6-6 6" /></>,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5m0-8h.01" /></>,
  } as const;
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}
