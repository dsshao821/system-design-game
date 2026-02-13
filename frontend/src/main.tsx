import React from "react";
import { createRoot } from "react-dom/client";

function App() {
  return (
    <main style={{ fontFamily: "Inter, sans-serif", padding: 24 }}>
      <h1>System Design Game - Frontend</h1>
      <p>Starter shell for challenge player UI.</p>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
