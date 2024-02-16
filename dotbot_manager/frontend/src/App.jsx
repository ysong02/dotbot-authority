import { useState } from 'react'
import './App.css'

let acl = [1, 2, 3]
let joined_dotbots = {
  1: {
    timestamp: 1708095439,
  }
}

function Dashboard() {
  return (
    <div>
      <h1>Dotbot Manager</h1>
      <div style={{ display: "flex", alignItems: "center" }}>
        <h2 style={{ marginRight: "10px" }}>Access Control List:</h2>
        <div>
          {acl.map((id) => (
            <span style={{ margin: 5, padding: 5, border: "1px solid white" }} key={id}>{id}</span>
          ))}
        </div>
      </div>
      <div >
        <h2 >Joined DotBots:</h2>
        <div>
          {/* {acl.map((id) => ( */}
          {Object.entries(joined_dotbots).map((dotbot) => {
            let id = dotbot[0]
            let timestamp = new Date(dotbot[1].timestamp * 1000).toDateString()
            return <span style={{ margin: 5, padding: 5, border: "1px solid white" }} key={id}>{timestamp}: {id}</span>
          })}
        </div>
      </div>
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
