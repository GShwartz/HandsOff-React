import React, { useState, useEffect, useRef, useCallback } from 'react';
import { throttle } from 'lodash';
import LazyImage from '../components/Content/LazyImage';
import LeftTable from '../components/Content/LeftTable';
import RightTable from '../components/Content/RightTable';
import ImageModal from '../components/Content/ImageModal';
import "../components/CSS/content.css";
import "../components/CSS/tables.css";

const fileCache = {};

function Content({ endpoints }) {
  const [chosenRow, setChosenRow] = useState(null);
  const lastChosenRowRef = useRef(null); // Track the last successfully chosen row
  const [checkedRows, setCheckedRows] = useState({});
  const [selectAllChecked, setSelectAllChecked] = useState(false);
  const [images, setImages] = useState([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [maxVisibleImages, setMaxVisibleImages] = useState(0);
  const [modalImage, setModalImage] = useState(null);
  const sliderRef = useRef(null);

  const resetAllStates = useCallback(() => {
    setChosenRow(null);
    setCheckedRows({});
    setSelectAllChecked(false);
    setImages([]);
    setCurrentSlide(0);
    setMaxVisibleImages(0);
    setModalImage(null);
  }, []);

  const sendSelectedRowToBackend = useCallback(async (endpoint) => {
    try {
      const response = await fetch('http://handsoff.home.lab:8000/shell_data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(endpoint),
      });

      if (!response.ok) {
        throw new Error('Failed to update shell_data on the backend');
      }

      const data = await response.json();
      console.log("Backend Shell Data:", data);

      // Update the last chosen row only if the backend call is successful
      lastChosenRowRef.current = endpoint;

      return data;

    } catch (error) {
      console.error("Error sending selected row to backend:", error);
      throw error; // Rethrow error for further handling
    }
  }, []);

  const fetchFilesForEndpoint = useCallback(async (ident) => {
    if (fileCache[ident]) {
      setImages(fileCache[ident]);
      setCurrentSlide(0);
      return;
    }

    try {
      const response = await fetch(`http://handsoff.home.lab:8000/get_files?directory=${ident}`);
      const fileData = await response.json();
      fileCache[ident] = fileData.images || [];
      setImages(fileCache[ident]);
      setCurrentSlide(0);
    } catch (error) {
      console.error("Error fetching files:", error);
      resetAllStates();
    }
  }, [resetAllStates]);

  useEffect(() => {
    resetAllStates();
  }, [resetAllStates]);

  useEffect(() => {
    if (chosenRow) {
      fetchFilesForEndpoint(chosenRow.ident);
    } else {
      resetAllStates();
    }
  }, [chosenRow, fetchFilesForEndpoint, resetAllStates]);

  const calculateVisibleImages = useCallback(() => {
    if (sliderRef.current) {
      const sliderWidth = sliderRef.current.clientWidth;
      const imageWidth = sliderRef.current.querySelector('img')?.clientWidth || 0;
      const visibleImages = imageWidth > 0 ? Math.floor(sliderWidth / imageWidth) : 0;
      setMaxVisibleImages(visibleImages);
    }
  }, []);

  useEffect(() => {
    if (images.length > 0) {
      calculateVisibleImages();
    }
  }, [images.length, calculateVisibleImages]);

  useEffect(() => {
    const throttledResize = throttle(calculateVisibleImages, 200);
    window.addEventListener('resize', throttledResize);
    return () => window.removeEventListener('resize', throttledResize);
  }, [calculateVisibleImages]);

  useEffect(() => {
    if (sliderRef.current) {
      const imageWidth = sliderRef.current.querySelector('img')?.clientWidth || 0;
      sliderRef.current.style.transform = `translateX(-${currentSlide * imageWidth}px)`;
    }
  }, [currentSlide, images]);

  const handleNextSlide = useCallback(() => {
    if (currentSlide < images.length - maxVisibleImages) {
      setCurrentSlide((prevSlide) => prevSlide + 1);
    }
  }, [currentSlide, images.length, maxVisibleImages]);

  const handlePrevSlide = useCallback(() => {
    if (currentSlide > 0) {
      setCurrentSlide((prevSlide) => prevSlide - 1);
    }
  }, [currentSlide]);

  useEffect(() => {
    if (images.length === 0) {
      setCurrentSlide(0);
    } else if (currentSlide >= images.length) {
      setCurrentSlide(images.length - 1);
    }
  }, [images, currentSlide]);

    const handleRowClick = useCallback((endpoint) => {
      const isChecked = !!checkedRows[endpoint.client_mac]; // Get the current checkbox state
      
      if (chosenRow?.client_mac === endpoint.client_mac) {
          // Send 'clear_shell' message to backend when unselecting a row
          const clearShellData = {
              row: 'clear_shell'
          };

          sendSelectedRowToBackend(clearShellData).then(() => {
              resetAllStates();
          }).catch((error) => {
              console.error("Error sending 'clear_shell' to backend:", error);
          });
          return;
      }

      const rowDataWithCheckbox = {
          ...endpoint,
          checked: isChecked
      };

      // Optimistically update the UI immediately
      setChosenRow(rowDataWithCheckbox);

      sendSelectedRowToBackend(rowDataWithCheckbox).catch((error) => {
          if (lastChosenRowRef.current?.client_mac !== endpoint.client_mac) {
              setChosenRow(lastChosenRowRef.current);
          }
      });
  }, [chosenRow, sendSelectedRowToBackend, resetAllStates, checkedRows]);

  const handleCheckboxChange = useCallback((endpoint) => {
    setCheckedRows((prevCheckedRows) => {
      const newCheckedRows = {
        ...prevCheckedRows,
        [endpoint.client_mac]: !prevCheckedRows[endpoint.client_mac],
      };

      setSelectAllChecked(
        Object.keys(newCheckedRows).length === endpoints.length &&
        Object.values(newCheckedRows).every((checked) => checked)
      );

      return newCheckedRows;
    });
  }, [endpoints]);

  const handleSelectAllChange = useCallback(() => {
    const newCheckedState = !selectAllChecked;
    setSelectAllChecked(newCheckedState);

    const newCheckedRows = {};
    endpoints.forEach(endpoint => {
      newCheckedRows[endpoint.client_mac] = newCheckedState;
    });
    setCheckedRows(newCheckedRows);
  }, [endpoints, selectAllChecked]);

  const isRowChecked = (endpoint) => !!checkedRows[endpoint.client_mac];

  const handleImageClick = (src) => {
    setModalImage(src);
  };

  const handleCloseModal = () => {
    setModalImage(null);
  };

  return (
    <div className="content-container">
      <div className="left-container">
        <LeftTable
          endpoints={endpoints}
          chosenRow={chosenRow}
          setChosenRow={setChosenRow}
          handleRowClick={handleRowClick}
          handleCheckboxChange={handleCheckboxChange}
          isRowChecked={isRowChecked}
          handleSelectAllChange={handleSelectAllChange}
          selectAllChecked={selectAllChecked}
        />
      </div>

      <div className="right-container">
        <RightTable chosenRow={chosenRow} />
        <div className="image-slider-container">
          <button 
            className={`arrow left ${currentSlide === 0 ? 'disabled' : ''}`}
            onClick={handlePrevSlide}
            disabled={currentSlide === 0}
          >
            &#9664;
          </button>
          <div className="image-slider" ref={sliderRef}>
            {images.length > 0 ? (
              images.map((imgSrc, index) => (
                <LazyImage 
                  key={index} 
                  src={imgSrc} 
                  alt={`Slide ${index + 1}`} 
                  onClick={() => handleImageClick(imgSrc)} // Open modal on image click
                />
              ))
            ) : (
              <div className='image-slider'>
                <p className="no-images-message">No images available</p>
              </div>
            )}
          </div>
          <button 
            className={`arrow right ${currentSlide >= images.length - maxVisibleImages ? 'disabled' : ''}`}
            onClick={handleNextSlide}
            disabled={currentSlide >= images.length - maxVisibleImages}
          >
            &#9654;
          </button>
        </div>
      </div>

      {modalImage && (
        <ImageModal 
          src={modalImage} 
          alt="Selected Image" 
          onClose={handleCloseModal} 
        />
      )}
    </div>
  );
}

export default Content;
