import React, { useState } from 'react';
import '../CSS/tables.css'

const RightTable = ({ chosenRow }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const additionalInfo = chosenRow && chosenRow.additional_info;

  return (
    <div className="right-table-container">
      <table className="connected-stations-table-right">
        <thead>
          <tr>
            <th>Connection Time</th>
            <th>User</th>
            <th>OS</th>
            <th>VM</th>
            <th>Boot Time</th>
            <th>Client Version</th>
            {/* Embedded button */}
            <th>
              {chosenRow && (
                <button 
                  className="expand-button" 
                  onClick={() => setIsExpanded(!isExpanded)}
                  aria-label={isExpanded ? "Collapse additional info" : "Expand additional info"}
                >
                  {isExpanded ? "-" : "+"}
                </button>
              )}
            </th>
          </tr>
        </thead>
        <tbody>
          {chosenRow ? (
            <>
              <tr>
                <td>{chosenRow.connection_time}</td>
                <td>{chosenRow.user}</td>
                <td>{chosenRow.os_release}</td>
                <td>{chosenRow.is_vm}</td>
                <td>{chosenRow.boot_time}</td>
                <td>{chosenRow.client_version}</td>
                <td></td>
              </tr>
              {isExpanded && additionalInfo && (
                <>
                  <tr>
                    <td colSpan="6">
                      <strong>Additional Info:</strong>
                    </td>
                  </tr>
                  {additionalInfo.map((info, index) => (
                    <tr key={index}>
                      <td>{info.new_connection_time}</td>
                      <td>{info.new_user}</td>
                      <td>{info.new_os_release}</td>
                      <td>{info.new_is_vm}</td>
                      <td>{info.new_boot_time}</td>
                      <td>{info.new_client_version}</td>
                    </tr>
                  ))}
                </>
              )}
            </>
          ) : (
            <tr>
              <td colSpan="7">No station selected</td>
            </tr>
          )}
        </tbody>
        {isExpanded && (
          <thead>
            <tr>
              <th>Domain</th>
              <th>Logon Server</th>
              <th>Connection Name</th>
              <th>DHCP Enabled</th>
              <th>DHCP Server</th>
              <th colSpan="2"></th>
            </tr>
          </thead>
        )}
      </table>
    </div>
  );
};

export default RightTable;
