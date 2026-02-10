import React, { useState, useEffect } from 'react';
import './BTUCalculator.css';

const BTUCalculator = () => {
  const [area, setArea] = useState('');
  const [occupants, setOccupants] = useState('');
  const [height, setHeight] = useState('');
  const [sunExposure, setSunExposure] = useState('average');
  const [totalBTU, setTotalBTU] = useState(0);

  useEffect(() => {
    calculateBTU();
  }, [area, occupants, height, sunExposure]);

  const calculateBTU = () => {
    // Parse inputs
    const areaVal = parseFloat(area) || 0;
    const occupantsVal = parseFloat(occupants) || 0;
    const heightVal = parseFloat(height) || 0;

    // Base BTU: Square Footage × 25
    const baseBTU = areaVal * 25;

    // Occupancy: (Number of People - 2) × 600
    // Only applies if occupants > 2
    let occupancyBTU = 0;
    if (occupantsVal > 2) {
      occupancyBTU = (occupantsVal - 2) * 600;
    }

    // Height: (Height - 8) × 1000
    // Only applies if height > 8
    let heightBTU = 0;
    if (heightVal > 8) {
      heightBTU = (heightVal - 8) * 1000;
    }

    // Climate/Sun Adjustments
    // We'll calculate this based on the Base BTU or the Subtotal.
    // Let's assume adjustment is on the Base BTU for simplicity, as specific load adjustments usually are.
    // Or we could apply it to the total. Given the prompt syntax "... + Climate/Sun Adjustments", it's an additive term.
    // Common practice: 
    // Shady: -10% 
    // Sunny: +10%
    // We will calculate this percentage based on the Base BTU.
    let sunBTU = 0;
    if (sunExposure === 'shady') {
      sunBTU = -(baseBTU * 0.10);
    } else if (sunExposure === 'sunny') {
      sunBTU = (baseBTU * 0.10);
    } else if (sunExposure === 'very_sunny') {
        sunBTU = (baseBTU * 0.20);
    }

    // Total
    setTotalBTU(baseBTU + occupancyBTU + heightBTU + sunBTU);
  };

  return (
    <div className="btu-container">
      <div className="btu-card">
        <h1 className="btu-title">BTU Calculator</h1>
        
        <div className="input-group">
          <label className="input-label">Room Area (sq ft)</label>
          <input
            type="number"
            className="btu-input"
            value={area}
            onChange={(e) => setArea(e.target.value)}
            placeholder="e.g. 200"
          />
        </div>

        <div className="input-group">
          <label className="input-label">Number of Occupants</label>
          <input
            type="number"
            className="btu-input"
            value={occupants}
            onChange={(e) => setOccupants(e.target.value)}
            placeholder="e.g. 2"
          />
        </div>

        <div className="input-group">
          <label className="input-label">Ceiling Height (ft)</label>
          <input
            type="number"
            className="btu-input"
            value={height}
            onChange={(e) => setHeight(e.target.value)}
            placeholder="e.g. 8"
          />
        </div>

        <div className="input-group">
          <label className="input-label">Sun Exposure / Climate</label>
          <select
            className="btu-select"
            value={sunExposure}
            onChange={(e) => setSunExposure(e.target.value)}
          >
            <option value="shady">Shaded / Cool (-10%)</option>
            <option value="average">Average</option>
            <option value="sunny">Sunny / Warm (+10%)</option>
            <option value="very_sunny">Very Sunny / Hot (+20%)</option>
          </select>
        </div>

        <div className="result-section">
          <h2 className="result-title">Recommended Cooling Capacity</h2>
          <div className="result-value">
            {Math.round(totalBTU).toLocaleString()} BTU
          </div>
          
          <div className="breakdown">
            <div className="breakdown-item">
                <span>Base (Area × 25):</span>
                <span>{Math.round(area * 25 || 0)}</span>
            </div>
            <div className="breakdown-item">
                <span>Occupancy Adj.:</span>
                <span>{Math.round(Math.max(0, (occupants - 2) * 600) || 0)}</span>
            </div>
             <div className="breakdown-item">
                <span>Height Adj.:</span>
                <span>{Math.round(Math.max(0, (height - 8) * 1000) || 0)}</span>
            </div>
             <div className="breakdown-item">
                <span>Climate/Sun Adj.:</span>
                <span>{Math.round((sunExposure === 'shady' ? -(area * 25 * 0.10) : sunExposure === 'sunny' ? (area * 25 * 0.10) : sunExposure === 'very_sunny' ? (area * 25 * 0.20) : 0) || 0)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BTUCalculator;
