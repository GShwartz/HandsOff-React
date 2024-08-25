import React, { useState, useRef, useEffect, useCallback } from 'react';
import ModalWorking from './ModalWorking';
import { sendRequestToBackend } from '../api';

const actionButtons = [
  { label: 'SCREENSHOT', action: 'screenshot' },
  { label: 'TASKS', action: 'tasks' },
  { label: 'SYSINFO', action: 'sysinfo' },
  { label: 'UPDATE', action: 'update' },
  { label: 'RESTART', action: 'restart' },
  { label: 'LOCAL', action: 'local_dropdown' },
];

const ActionDropdown = ({ index, endpoint, chosenRow, setChosenRow, onDropdownToggle, refreshImages }) => {
  const [dropdownOpenIndex, setDropdownOpenIndex] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isScreenshotAction, setIsScreenshotAction] = useState(false); // Track if it's a screenshot action
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

  const handleActionClick = async (action) => {
    try {
      if (action === 'screenshot') {
        setIsScreenshotAction(true); // Track that screenshot was triggered
      }

      await sendRequestToBackend(
        'http://handsoff.home.lab:8000/control',
        'POST',
        { action, endpoint: chosenRow },
        action,
        setIsModalVisible
      );
      console.log(`${action} action sent successfully`);

      // Refresh images if screenshot was taken
      if (action === 'screenshot') {
        if (typeof refreshImages === 'function') {
          refreshImages(); // Call the function correctly
        } else {
          console.error("refreshImages is not a function");
        }
      }

    } catch (error) {
      console.error(`Failed to send ${action} action to backend:`, error);
    } finally {
      setDropdownOpenIndex(null); // Close dropdown after action is processed
      onDropdownToggle(false);
    }
  };

  // Function to handle the modal close and refresh the page
  const handleModalClose = () => {
    setIsModalVisible(false);

    if (isScreenshotAction) {
      setIsScreenshotAction(false);
      // Refresh the page after the modal is fully closed
      setTimeout(() => {
        window.location.reload(); // Refresh the page
      }, 100); // Delay to ensure the modal is fully closed before the refresh
    }
  };

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
              onClick={(e) => {
                e.stopPropagation();
                handleActionClick(button.action);
              }}
            >
              {button.label}
            </button>
          </li>
        ))}
      </ul>
      {/* Render the modal */}
      <ModalWorking show={isModalVisible} onClose={handleModalClose} />
    </div>
  );
};

export default ActionDropdown;
