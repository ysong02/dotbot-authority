import { useState, useEffect, useCallback } from 'react'
import useWebSocket from 'react-use-websocket';
import moment from 'moment'

import './App.css'

import {
  apiFetchACL
} from "./rest";

import { NotificationType } from './constants'

const websocketUrl = `ws://localhost:18000/ws/joined-dotbots-log`;

function AuthorizationLogEntry({ id, timestamp, authorized}) {
  timestamp = moment(timestamp).format('YYYY-MM-DD HH:mm:ss');
  return (
    <tr>
      <td>{timestamp}</td>
      <td>{id}</td>
      <td>{authorized ? "✅ Authorized" : "❌ Unauthorized"}</td>
    </tr>
  );
}
function AttestationLogEntry({ id, attestation_result, software_name, fs_name, fs_size, tag_version}) {
  return(
    <tr>
      <td>{id}</td>
      <td>{software_name}</td>
      <td>{fs_name}</td>
      <td>{fs_size}</td>
      <td>{tag_version}</td>
      <td>{attestation_result ? "✅ Verified" : "❌ Not Verified"}</td>
    </tr>
  )
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

function AttestationLog({ results }) {
  return (
    <div>
      <h2>DotBots Attestation Log:</h2>
      <div style={{ display: "inline-block", minWidth: "50%" }}>
        <table style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Sofware Name</th>
              <th>Source File</th>
              <th>Source File Size</th>
              <th>Evidence Tag Version</th>
              <th>Attestation Result</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result) => (
              <AttestationLogEntry key={result.id} id={result.id} software_name={result.software_name} fs_name={result.fs_name} fs_size={result.fs_size} tag_version={result.tag_version} attestation_result={result.attestation_result} />
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
  // set state variables
  const [dotbots_authorization_log, setDotbotsAuthorizationLog] = useState([]);
  const [dotbots_attestation_log, setDotbotsAttestationLog] = useState([]);

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
    // if (message.cmd === NotificationType.AuthorizationResult) {
    //   setDotbotsAuthorizationLog((prev) => {
    //     return [message.data, ...prev];
    //   });
    //   fetchACL();
    // }
    switch (message.cmd){
      case NotificationType.AuthorizationResult:
        setDotbotsAuthorizationLog((prev) => [message.data, ...prev]);
        fetchACL();
        break;

      case NotificationType.AttestationResult:
        setDotbotsAttestationLog((prev) => [message.data, ...prev]);
      break;
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
      <AttestationLog results={dotbots_attestation_log} />
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
