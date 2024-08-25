import React, { useState, useEffect, useRef, useCallback } from 'react';
import { throttle } from 'lodash';
import { useRowSelection } from './Content/useRowSelection';
import LazyImage from './Content/LazyImage';
import LeftTable from './Content/LeftTable';
import RightTable from './Content/RightTable';
import ImageModal from './Content/ImageModal';
import { sendSelectedRowToBackend, fetchFilesForEndpoint } from './api';

import "./CSS/content.css";
import "./CSS/tables.css";

const fileCache = {};

function Content({ endpoints }) {
    const {
        chosenRow,
        setChosenRow,
        checkedRows,
        selectAllChecked,
        handleCheckboxChange,
        handleSelectAllChange,
    } = useRowSelection(endpoints);

    const [images, setImages] = useState([]);
    const [currentSlide, setCurrentSlide] = useState(0);
    const [maxVisibleImages, setMaxVisibleImages] = useState(0);
    const [modalImage, setModalImage] = useState(null);
    const sliderRef = useRef(null);
    const lastChosenRowRef = useRef(null);

    const resetAllStatesExceptRow = useCallback(() => {
        setImages([]);  // Reset images
        setCurrentSlide(0);
        setMaxVisibleImages(0);
        setModalImage(null);
    }, []);

    const refreshImages = useCallback(() => {
        if (chosenRow) {
            fetchFilesForEndpoint(chosenRow.ident)
                .then(fetchedImages => {
                    const existingImages = fileCache[chosenRow.ident] || [];
                    const newImages = fetchedImages.filter(img => !existingImages.includes(img)); // Avoid duplicates

                    const updatedImages = [...newImages.reverse(), ...existingImages]; // Prepend new images and reverse
                    fileCache[chosenRow.ident] = updatedImages; // Update the cache
                    setImages(updatedImages);
                    setCurrentSlide(0); // Reset to the first slide (newest image)
                })
                .catch(error => resetAllStatesExceptRow());
        } else {
            resetAllStatesExceptRow();
        }
    }, [chosenRow, resetAllStatesExceptRow]);

    useEffect(() => {
        refreshImages(); // Initial load of images
    }, [chosenRow, refreshImages]);

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
            calculateVisibleImages();  // Recalculate when images are updated
        }
    }, [images, calculateVisibleImages]);

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
        const isChecked = !!checkedRows[endpoint.client_mac];

        if (chosenRow?.client_mac === endpoint.client_mac) {
            const clearShellData = { message: 'clear_shell' };

            sendSelectedRowToBackend(clearShellData).then(() => {
                resetAllStatesExceptRow();
                setChosenRow(null); // Clear chosen row
            }).catch((error) => {
                console.error("Error sending 'clear_shell' to backend:", error);
            });
            return;
        }

        const rowDataWithCheckbox = {
            ...endpoint,
            checked: isChecked
        };

        setChosenRow(rowDataWithCheckbox);

        sendSelectedRowToBackend(rowDataWithCheckbox).catch((error) => {
            if (lastChosenRowRef.current?.client_mac !== endpoint.client_mac) {
                setChosenRow(lastChosenRowRef.current);
            }
        });
    }, [chosenRow, resetAllStatesExceptRow, checkedRows, setChosenRow]);

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
                    isRowChecked={(endpoint) => !!checkedRows[endpoint.client_mac]}
                    handleSelectAllChange={handleSelectAllChange}
                    selectAllChecked={selectAllChecked}
                    refreshImages={refreshImages} // Pass refreshImages down to the LeftTable component
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
                                    onClick={() => handleImageClick(imgSrc)}
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
