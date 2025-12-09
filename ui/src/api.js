const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function chat(query) {
const res = await fetch(`${API_BASE_URL}/chat/`, {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({ query }),
});
return res.json();
}

export async function uploadDocument(file) {
const formData = new FormData();
formData.append("file", file);
const res = await fetch(`${API_BASE_URL}/ingest/`, {
method: "POST",
body: formData,
});
return res.json();
}