import { useState } from "react";
import { chat, uploadDocument } from "../api";


export default function ChatWindow() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [uploading, setUploading] = useState(false);

  async function send() {
    if (!input.trim()) return;
    try {
      const resp = await chat(input);
      setMessages([...messages, { q: input, a: resp.answer }]);
      setInput("");
    } catch (error) {
      console.error("Error sending message:", error);
      alert("Failed to send message. Check console for details.");
    }
  }

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadDocument(file);
      if (result.status === "indexed") {
        alert(`Document uploaded! ${result.chunks} chunks indexed.`);
      } else {
        alert(`Error: ${result.message}`);
      }
    } catch (error) {
      console.error("Error uploading document:", error);
      alert("Failed to upload document. Check console for details.");
    } finally {
      setUploading(false);
      e.target.value = null;
    }
  }

  return (
    <div className="bg-white rounded p-4 shadow w-full max-w-2xl mx-auto">
      <div className="mb-4 flex items-center gap-2">
        <label className="bg-green-500 text-white px-4 py-2 rounded cursor-pointer hover:bg-green-600">
          {uploading ? "Uploading..." : "📄 Upload Document"}
          <input
            type="file"
            onChange={handleFileUpload}
            disabled={uploading}
            className="hidden"
            accept=".pdf,.txt,.doc,.docx"
          />
        </label>
        <span className="text-sm text-gray-600">Upload PDFs, TXT, DOC files</span>
      </div>
      <div className="h-96 overflow-y-auto border p-2 mb-4">
        {messages.map((m, i) => (
          <div key={i} className="mb-2">
            <b>You:</b> {m.q}
            <br />
            <b>AI:</b> {m.a}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === "Enter" && send()}
        className="border p-2 w-3/4"
        placeholder="Type your message..."
      />
      <button onClick={send} className="bg-blue-500 text-white px-4 py-2 ml-2 rounded hover:bg-blue-600">Send</button>
    </div>
  );
}