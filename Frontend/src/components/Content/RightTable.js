import React from 'react';

const RightTable = ({ chosenRow }) => (
  <table className="connected-stations-table-right">
    <thead>
      <tr>
        <th>Connection Time</th>
        <th>User</th>
        <th>OS</th>
        <th>VM</th>
        <th>Boot Time</th>
        <th>Client Version</th>
      </tr>
    </thead>
    <tbody>
      {chosenRow ? (
        <tr>
          <td>{chosenRow.connection_time}</td>
          <td>{chosenRow.user}</td>
          <td>{chosenRow.os_release}</td>
          <td>{chosenRow.is_vm}</td>
          <td>{chosenRow.boot_time}</td>
          <td>{chosenRow.client_version}</td>
        </tr>
      ) : (
        <tr>
          <td colSpan="6">No station selected</td>
        </tr>
      )}
    </tbody>
  </table>
);

export default RightTable;
