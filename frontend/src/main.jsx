import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { ClerkProvider } from '@clerk/clerk-react'

// REPLACE THIS WITH YOUR ACTUAL CLERK KEY
const PUBLISHABLE_KEY = "pk_test_cmVsYXRpdmUtcmFwdG9yLTY2LmNsZXJrLmFjY291bnRzLmRldiQ"

if (!PUBLISHABLE_KEY) {
  throw new Error("Missing Publishable Key")
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
      <App />
    </ClerkProvider>
  </React.StrictMode>,
)