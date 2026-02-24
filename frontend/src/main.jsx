import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Mount the React app to the #root div in index.html
createRoot(document.getElementById('root')).render(
  <App />
)