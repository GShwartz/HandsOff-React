import React from "react";
import ReactDOM from "react-dom/client";
import App from "./components/app.js"; // Ensure this path is correct

// Import global styles if necessary
import './components/CSS/app.css'; // Adjust path as needed

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);