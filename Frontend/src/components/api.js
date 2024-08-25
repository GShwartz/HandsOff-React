// api.js
export async function sendRequestToBackend(url, method = 'POST', data = null, action = '', setIsModalVisible = () => {}, onRequestComplete = () => {}) {
    try {
        if (action === 'screenshot') {
            setIsModalVisible(true); // Show the modal
        }

        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: data ? JSON.stringify(data) : null,
        });

        if (!response.ok) {
            throw new Error(`Failed to ${method} data to the backend`);
        }

        const responseData = await response.json();
        console.log(`Backend Response from ${url}:`, responseData);
        return responseData;

    } catch (error) {
        console.error(`Error during ${method} request to ${url}:`, error);
        throw error;
    } finally {
        if (action === 'screenshot') {
            setIsModalVisible(false); // Hide the modal
        }
        onRequestComplete(); // Notify that request is complete
    }
}

export async function sendSelectedRowToBackend(endpoint) {
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
        return data;

    } catch (error) {
        console.error("Error sending selected row to backend:", error);
        throw error;
    }
}

export async function fetchFilesForEndpoint(ident) {
    try {
        const response = await fetch(`http://handsoff.home.lab:8000/get_files?directory=${ident}`);
        const fileData = await response.json();

        return fileData.images || [];

    } catch (error) {
        console.error("Error fetching files:", error);
        return [];
    }
}
