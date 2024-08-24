import React, { useState, useEffect } from 'react';
import Topnav from './topnav';
import ServerInfo from './server-info';
import Content from './content';
import '../components/CSS/app.css';
import '../components/CSS/tables.css';


function App() {
    const [connectedStations, setConnectedStations] = useState(0);
    const [endpoints, setEndpoints] = useState([]);
    const [servingOn, setServingOn] = useState([]);
    const [bootTime, setBootTime] = useState([]);
    const [serverVersion, setServerVersion] = useState([]);

    useEffect(() => {
        fetch('http://handsoff.home.lab:8000/', {
            method: 'GET'
        })
        .then(response => response.json())  // Parse the JSON from the response
        .then(data => {
            console.log('Fetched data:', data);  // Log the data to check its structure
            const apiData = data.data;  // Access the 'data' object inside the response
            setServingOn(apiData.serving_on);
            setBootTime(apiData.boot_time);
            setServerVersion(apiData.server_version);
            setConnectedStations(apiData.connected_stations);  // Update state with the number of connected stations
            setEndpoints(apiData.endpoints);  // Update state with the list of endpoints
        })
        .catch(error => {
            console.error('Error fetching connected stations:', error);
        });
    }, []);

    return (
        <div className="App">
            <Topnav />
            <div className="server-information-container">
                <ServerInfo 
                    servingOn={servingOn}
                    bootTime={bootTime} 
                    serverVersion={serverVersion}
                    connectedStations={connectedStations} 
                />
            </div>
            <Content endpoints={endpoints} />
        </div>
    );
}

export default App;
