import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

function App() {
  const [holders, setHolders] = useState(null);
  const [error, setError] = useState(false);

  // Fetch the temporary API once when the view mounts.
  useEffect(() => {
    fetch('/api/account-holders')
      .then((response) => {
        if (!response.ok) throw new Error('Request failed');
        return response.json();
      })
      .then(setHolders)
      .catch(() => setError(true));
  }, []);

  if (error) return <p>Unable to load account holders.</p>;
  if (holders === null) return <p>Loading account holders…</p>;

  return (
    <>
      <h1>Account holders</h1>
      <ul>
        {holders.map((holder) => <li key={holder}>{holder}</li>)}
      </ul>
    </>
  );
}

createRoot(document.getElementById('root')).render(<App />);
