import React, { useState, useEffect, useRef, memo } from 'react';

const LazyImage = memo(({ src, alt, onClick }) => {
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef();

  useEffect(() => {
    const img = imgRef.current;
    if (img.complete) {
      setLoaded(true);
    }
  }, []);

  const handleLoad = () => {
    setLoaded(true);
  };

  return (
    <img
      ref={imgRef}
      src={src}
      alt={alt}
      loading="lazy" // Lazy load the image
      onLoad={handleLoad}
      onClick={onClick}
      style={{
        opacity: loaded ? 1 : 0,
        transition: 'opacity 0.5s ease',
        cursor: 'pointer'
      }}
    />
  );
});

export default LazyImage;
