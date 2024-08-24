import React, { useState, useRef, useEffect, useCallback } from 'react';

const actionButtons = [
  { label: 'SCREENSHOT', action: 'screenshot' },
  { label: 'TASKS', action: 'tasks' },
  { label: 'SYSINFO', action: 'sysinfo' },
  { label: 'UPDATE', action: 'update' },
  { label: 'RESTART', action: 'restart' },
  { label: 'LOCAL', action: 'local_dropdown' },
];

const ActionDropdown = ({ index, endpoint, chosenRow, setChosenRow, onDropdownToggle }) => {
  const [dropdownOpenIndex, setDropdownOpenIndex] = useState(null);
  const dropdownRefs = useRef([]);

  const toggleDropdown = (index, endpoint) => {
    if (dropdownOpenIndex === index) {
      setDropdownOpenIndex(null);
      onDropdownToggle(false); // Notify parent that dropdown is closed
    } else {
      setDropdownOpenIndex(index);
      onDropdownToggle(true); // Notify parent that dropdown is open
      setChosenRow(endpoint); // Update chosen row when dropdown is opened
    }
  };

  const handleClickOutside = useCallback((event) => {
    if (
      dropdownOpenIndex !== null &&
      dropdownRefs.current[dropdownOpenIndex] &&
      !dropdownRefs.current[dropdownOpenIndex].contains(event.target)
    ) {
      setDropdownOpenIndex(null);
      onDropdownToggle(false); // Notify parent that dropdown is closed
    }
  }, [dropdownOpenIndex, onDropdownToggle]);

  useEffect(() => {
    if (dropdownOpenIndex !== null) {
      document.addEventListener('click', handleClickOutside, true);
    } else {
      document.removeEventListener('click', handleClickOutside, true);
    }
    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  }, [dropdownOpenIndex, handleClickOutside]);

  return (
    <div className="action-dropdown" ref={(el) => (dropdownRefs.current[index] = el)}>
      <button
        className="action-button"
        onClick={(e) => {
          e.stopPropagation();
          toggleDropdown(index, endpoint);
        }}
      >
        Actions {dropdownOpenIndex === index ? '►' : '▼'}
      </button>
      <ul className={`action-dropdown-menu ${dropdownOpenIndex === index ? 'show' : ''}`}>
        {actionButtons.map((button, btnIndex) => (
          <li key={btnIndex}>
            <button 
              className="dropdown-item"
              onClick={(e) => e.stopPropagation()}>
              {button.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ActionDropdown;
