import { useState, useCallback } from 'react';

export const useRowSelection = (endpoints) => {
  const [chosenRow, setChosenRow] = useState(null);
  const [checkedRows, setCheckedRows] = useState({});
  const [selectAllChecked, setSelectAllChecked] = useState(false);

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

  return {
    chosenRow,
    setChosenRow,
    checkedRows,
    selectAllChecked,
    handleCheckboxChange,
    handleSelectAllChange,
  };
};
