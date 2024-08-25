import React from 'react';
import '../CSS/content.css';

const ModalWorking = ({ show, onClose }) => {

  if (!show) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <p>Working...</p>
      </div>
    </div>
  );
};

export default ModalWorking;
