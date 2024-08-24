import React from 'react';
import '../components/CSS/tables.css';

function ServerInfo({ servingOn, bootTime, serverVersion, connectedStations }) {
  return (
      <table className="server-info-table">
        <thead className='th'>
          <tr>
            <th>Serving on</th>
            <th>Boot Time</th>
            <th>Connected Stations</th>
            <th>Server Version</th>
          </tr>
        </thead>
        <tbody className='tbody'>
          <tr>
            <td>{servingOn}</td>
            <td>{bootTime}</td>
            <td>{connectedStations}</td>
            <td>{serverVersion}</td>
          </tr>
        </tbody>
      </table>
  );
}

export default ServerInfo;
