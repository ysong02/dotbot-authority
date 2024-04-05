import { useState, useEffect, useCallback } from 'react'
import useWebSocket from 'react-use-websocket';
import moment from 'moment'

import './App.css'

import {
  apiFetchACL
} from "./rest";

import { NotificationType } from './constants'

const websocketUrl = `ws://localhost:18000/ws/joined-dotbots-log`;

function AuthorizationLogEntry({ id, timestamp, authorized }) {
  timestamp = moment(timestamp).format('YYYY-MM-DD HH:mm:ss');
  return (
    <tr>
      <td>{timestamp}</td>
      <td>{id}</td>
      <td>{authorized ? "✅ Authorized" : "❌ Unauthorized"}</td>
    </tr>
  );
}

function AuthorizationLog({ dotbots }) {
  return (
    <div>
      <h2>DotBots Authorization Log:</h2>
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
              <AuthorizationLogEntry key={dotbot.timestamp} id={dotbot.id} timestamp={dotbot.timestamp} authorized={dotbot.authorized} />
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
  const [dotbots_authorization_log, setDotbotsAuthorizationLog] = useState([]);

  const fetchACL = useCallback(async () => {
    const data = await apiFetchACL().catch(error => console.log(error));
    setACL(data);
  }, [setACL]);

  useEffect(() => {
    if (acl === undefined) {
      fetchACL();
    }
  }, [acl]);

  const onWsOpen = () => {
    console.log('websocket opened');
    fetchACL();
  };

  const onWsMessage = (event) => {
    const message = JSON.parse(event.data);
    console.log(`websocket got new message: ${JSON.stringify(message)}`);
    if (message.cmd === NotificationType.AuthorizationResult) {
      setDotbotsAuthorizationLog((prev) => {
        return [message.data, ...prev];
      });
      fetchACL();
    }
  };

  useWebSocket(websocketUrl, {
    onOpen: () => onWsOpen(),
    onClose: () => console.log("websocket closed"),
    onMessage: (event) => onWsMessage(event),
    shouldReconnect: (event) => true,
  });

  return (
    <div>
      <h1>DotBot Authority</h1>
      <DotbotACL acl={acl} />
      <AuthorizationLog dotbots={dotbots_authorization_log} />
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
