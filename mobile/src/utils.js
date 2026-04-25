// Tiny JWT decoder (no external dep). Returns `role` claim from SimpleJWT token,
// which we set via a custom claim — falls back to inspecting the username table.
// SimpleJWT default tokens don't contain `role` — so we rely on the backend
// echoing the role via a separate endpoint OR we encode the username and look
// it up. For MVP we simply derive from username convention if claim is absent.
export function jwtDecodeRole(token) {
  try {
    const payload = JSON.parse(
      decodeURIComponent(
        atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
          .split("")
          .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      )
    );
    if (payload.role) return payload.role;
    // Fallback heuristic from seeded usernames
    const u = payload.username || "";
    if (u.startsWith("admin")) return "admin";
    if (u.startsWith("inspector")) return "inspector";
    if (u.startsWith("transporter")) return "transporter";
    return "public";
  } catch {
    return "public";
  }
}

export const formatDate = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString();
};
