export const theme = {
  primary: "#0f9d58",
  primaryDark: "#0a7d45",
  bg: "#f5f7fa",
  card: "#ffffff",
  text: "#1f2937",
  muted: "#6b7280",
  border: "#e5e7eb",
  green: "#10b981",
  orange: "#f59e0b",
  red: "#ef4444",
  blue: "#3b82f6",
};

export const statusColor = (status) => {
  switch (status) {
    case "delivered":
    case "imported":
      return theme.green;
    case "quarantine":
    case "transported":
    case "health_check":
      return theme.orange;
    case "issue":
      return theme.red;
    default:
      return theme.blue;
  }
};

export const statusLabel = (s) =>
  ({
    imported: "Imported",
    quarantine: "Quarantine",
    health_check: "Health Check",
    transported: "Transported",
    delivered: "Delivered",
    issue: "Issue",
  }[s] || s);
