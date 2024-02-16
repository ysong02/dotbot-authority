import { useState, useEffect, useCallback } from 'react'
import moment from 'moment'

import './App.css'

import {
  apiFetchACL
} from "./rest";

// let acl = [1, 2, 3]
let joined_dotbots_log = [
  {
    id: 1,
    timestamp: moment().unix(),
    authorized: true,
  },
  {
    id: 4,
    timestamp: moment().unix() - 1234,
    authorized: false,
  }
]
function JoinedDotbot({ id, timestamp, authorized }) {
  timestamp = moment(timestamp * 1000).format('YYYY-MM-DD HH:mm:ss');
  return (
    <tr>
      <td className="firstLogCell">{timestamp}</td>
      <td className="logCell">{id}</td>
      <td className="logCell">{authorized ? "✅ Authorized" : "❌ Unauthorized"}</td>
    </tr>
  );
}

function JoinedDotbots({ dotbots }) {
  return (
    <div>
      <h2>Joined DotBots Log:</h2>
      <div style={{ display: "inline-block", minWidth: "50%" }}>
        <table style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>ID</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {dotbots.map((dotbot) => (
              <JoinedDotbot key={dotbot.id} id={dotbot.id} timestamp={dotbot.timestamp} authorized={dotbot.authorized} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DotbotACL({ acl }) {
  if (acl === undefined) return (<div>Loading...</div>);
  return (
    <div style={{ display: "flex", alignItems: "center" }}>
      <h2 style={{ marginRight: "10px" }}>Allowed DotBots:</h2>
      <div>
        {acl.map((id) => (
          <span style={{ margin: 5, padding: 5, border: "1px solid white" }} key={id}>{id}</span>
        ))}
      </div>
    </div>
  );
}

function Dashboard() {
  const [acl, setACL] = useState();

  const fetchACL = useCallback(async () => {
    const data = await apiFetchACL().catch(error => console.log(error));
    setACL(data);
  }, [setACL]);

  useEffect(() => {
    if (acl === undefined) {
      fetchACL();
    }
  }, [acl]);

  return (
    <div>
      <h1>Dotbot Manager</h1>
      <DotbotACL acl={acl} />
      <JoinedDotbots dotbots={joined_dotbots_log} />
    </div>
  )
}

function App() {
  return (
    <>
      <Dashboard />
    </>
  )
}

export default App
