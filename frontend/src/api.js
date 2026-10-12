const BASE = import.meta.env.VITE_API_URL || "";

async function handle(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong. Please try again.");
  return data;
}

export const getRoles = () => fetch(`${BASE}/api/roles`).then(handle);

export function analyze({ role, file, text }) {
  const form = new FormData();
  form.append("role", role);
  if (file) form.append("file", file);
  else form.append("text", text);
  return fetch(`${BASE}/api/analyze`, { method: "POST", body: form }).then(handle);
}
