import React, { useState } from 'react';
import ActionDropdown from './ActionDropdown';

const LeftTable = ({ endpoints, chosenRow, setChosenRow, handleRowClick, handleCheckboxChange, isRowChecked, handleSelectAllChange, selectAllChecked }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  return (
    <table className="connected-stations-table">
      <thead>
        <tr>
          <th>
            <input
              type="checkbox"
              checked={selectAllChecked}
              onChange={handleSelectAllChange}
              aria-label="Select all endpoints"
            />
          </th>
          <th>Hostname</th>
          <th>Client MAC</th>
          <th>IP Address</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {endpoints.map((endpoint, index) => (
          <tr
            key={index}
            className={chosenRow?.client_mac === endpoint.client_mac ? 'chosen-row' : ''}
            onClick={(e) => {
              if (!isDropdownOpen && e.target.type !== 'checkbox') {
                handleRowClick(endpoint); // Trigger row click and backend update
              }
            }}
            style={{ cursor: isDropdownOpen ? 'not-allowed' : 'pointer' }} // Change cursor to indicate disabled state
          >
            <td>
              <input
                type="checkbox"
                checked={isRowChecked(endpoint)}
                onChange={(e) => {
                  e.stopPropagation();
                  handleCheckboxChange(endpoint);
                }}
                aria-label={`Select endpoint ${endpoint.client_mac}`}
              />
            </td>
            <td>{endpoint.ident}</td>
            <td>{endpoint.client_mac}</td>
            <td>{endpoint.ip}</td>
            <td>
              <ActionDropdown 
                index={index} 
                endpoint={endpoint} 
                chosenRow={chosenRow} 
                setChosenRow={setChosenRow} 
                onDropdownToggle={setIsDropdownOpen} // Pass function to handle dropdown toggle
              />
            </td>
          </tr>
        ))}
        {endpoints.length === 0 && (
          <tr>
            <td colSpan="5">No stations connected</td>
          </tr>
        )}
      </tbody>
    </table>
  );
};

export default LeftTable;
