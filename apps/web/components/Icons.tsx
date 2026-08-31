export type IconName =
    | "wallet" | "invoice" | "trend" | "receipt" | "alert" | "check" | "pulse"
    | "chat" | "sparkle" | "arrow" | "trophy" | "users" | "layers" | "bulb"
    | "coins" | "percent" | "clock" | "box" | "trendDown";

const ICON_PATHS: Record<IconName, string> = {
    wallet: "M3 7a2 2 0 012-2h13a1 1 0 011 1v3M3 7v10a2 2 0 002 2h15a1 1 0 001-1v-6a1 1 0 00-1-1h-4a2 2 0 100 4h5M3 7l3-4h9",
    invoice: "M7 3h10a1 1 0 011 1v16l-3-2-3 2-3-2-3 2V4a1 1 0 011-1zM9 8h6M9 12h6M9 16h3",
    trend: "M3 17l6-6 4 4 8-8M21 7h-6v6",
    trendDown: "M3 7l6 6 4-4 8 8M21 17h-6v-6",
    receipt: "M6 2h12v20l-3-2-3 2-3-2-3 2V2zM9 7h6M9 11h6M9 15h4",
    alert: "M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z",
    check: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
    pulse: "M3 12h4l3 8 4-16 3 8h4",
    chat: "M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z",
    sparkle: "M12 3l1.8 4.9L19 9.7l-4.9 1.8L12 16.4l-1.8-4.9L5 9.7l4.9-1.8L12 3zM19 15l.9 2.4 2.4.9-2.4.9-.9 2.4-.9-2.4-2.4-.9 2.4-.9.9-2.4z",
    arrow: "M5 12h14M13 6l6 6-6 6",
    trophy: "M8 21h8M12 17v4M7 4h10v4a5 5 0 01-10 0V4zM7 5H4a3 3 0 003 3M17 5h3a3 3 0 01-3 3",
    users: "M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2M10 11a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75",
    layers: "M12 2l9 5-9 5-9-5 9-5zM3 12l9 5 9-5M3 17l9 5 9-5",
    bulb: "M9 18h6M10 22h4M12 2a7 7 0 00-4 12.7c.6.5 1 1.2 1 2.05V17h6v-.25c0-.85.4-1.55 1-2.05A7 7 0 0012 2z",
    coins: "M12 8a4 3 0 100-6 4 3 0 000 6zM4 12a4 3 0 008 0M4 5v14a4 3 0 008 0M20 5v14a4 3 0 01-8 0V5",
    percent: "M19 5L5 19M7 8a2 2 0 100-4 2 2 0 000 4zM17 20a2 2 0 100-4 2 2 0 000 4z",
    clock: "M12 8v4l3 2M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    box: "M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8M12 13v8",
};

export default function Icon({ name, className }: { name: IconName; className?: string }) {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
            <path d={ICON_PATHS[name]} />
        </svg>
    );
}