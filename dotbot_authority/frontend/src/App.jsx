import { useState, useEffect, useCallback } from 'react'
import useWebSocket from 'react-use-websocket';
import moment from 'moment'

import './App.css'

import {
  apiFetchACL
} from "./rest";

import { NotificationType } from './constants'

const websocketUrl = `ws://localhost:18000/ws/joined-dotbots-log`;

/* function AuthorizationLogEntry({ id, timestamp, authorized}) {
  timestamp = moment(timestamp).format('YYYY-MM-DD HH:mm:ss');
  return (
    <tr>
      <td>{timestamp}</td>
      <td>{id}</td>
      <td>{authorized ? "✅ Authorized" : "❌ Unauthorized"}</td>
    </tr>
  );
} */
function AttestationLogEntry({ id, timestamp, attestation_result, fs_name, firmware_hash, decision}) {
  timestamp = moment(timestamp).format('YYYY-MM-DD HH:mm:ss');
  return(
    <tr>
      <td>{timestamp}</td>
      <td>{id}</td>
      <td>{fs_name}</td>
      <td>{attestation_result}</td>
      <td>{firmware_hash}</td>
      <td>{decision ? "✅ Accepted" : "❌ Rejected"}</td>
    </tr>
  )
}

/* function AuthorizationLog({ dotbots }) {
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
} */

  function AttestationLog({ results }) {
    const sortedResults = [...results].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    return (
      <div>
        <h2>DotBots Attestation Log:</h2>
        <div style={{ display: "inline-block", minWidth: "50%" }}>
          <table style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>ID</th>
                {/* <th>Sofware Name</th> */}
                <th>Source File</th>
                <th>Attestation Result</th>
                <th>Firmware Hash Value</th>
                <th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {sortedResults.map((result) => (
                <AttestationLogEntry 
                  key={result.timestamp} 
                  id={result.id} 
                  timestamp={result.timestamp} 
                  fs_name={result.fs_name} 
                  attestation_result={result.attestation_result} 
                  firmware_hash={result.firmware_hash} 
                  decision={result.decision}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
  

// function DotbotACL({ acl }) {
//   if (acl === undefined) return (<div>Loading...</div>);
//   return (
//     <div style={{ display: "flex", alignItems: "center" }}>
//       <h2 style={{ marginRight: "10px" }}>Allowed DotBots' firmware version:</h2>
//       <div>
//         {acl.map((id) => (
//           <span style={{ margin: 5, padding: 5, border: "1px solid white" }} key={id}>{id}</span>
//         ))}
//       </div>
//     </div>
//   );
// }

function DotbotACL({ acl }) {
  if (acl === undefined) return <div>Loading...</div>;

  // Define the versions for each row
  const versions = ["v0.9", "v1.0"];

  return (
    <div>
      <h2>Allowed DotBot's Firmware Version: v1.0</h2>
      <h2>DotBot Firmware Table</h2>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={{ border: "1px solid black", padding: "8px", textAlign: "left" }}>
              Version
            </th>
            <th style={{ border: "1px solid black", padding: "8px", textAlign: "left" }}>
              Firmware Hash Value
            </th>
          </tr>
        </thead>
        <tbody>
          {acl.map((id, index) => (
            <tr key={id}>
              <td style={{ border: "1px solid black", padding: "8px" }}>
                {versions[index] || "Unknown"}
              </td>
              <td style={{ border: "1px solid black", padding: "8px" }}>
                {id}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
/*       case NotificationType.AuthorizationResult:
        setDotbotsAuthorizationLog((prev) => [message.data, ...prev]);
        fetchACL();
        break; */

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
      <h1>DotBot Attestation</h1>
      <DotbotACL acl={acl} />
      {/* <AuthorizationLog dotbots={dotbots_authorization_log} /> */}
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
