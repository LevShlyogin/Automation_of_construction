import React, { useState } from 'react';
import './TurbineSearch.css';

type Turbine = {
  name: string;
  stocks: string[];
};

const turbines: Turbine[] = [
  { name: 'Турбина N-123', stocks: ['NT-123456', 'NT-123457', 'NT-123458'] },
  { name: 'Турбина A-100', stocks: ['NT-654321', 'NT-654322'] },
  { name: 'Турбина C-200', stocks: ['NT-333444'] },
  { name: 'Турбина E-223', stocks: ['NT-123456', 'NT-123457', 'NT-123458'] },
  { name: 'Турбина K-250', stocks: ['NT-654321', 'NT-654322'] },
  { name: 'Турбина Z-567', stocks: ['NT-333444'] },
];

type Props = {
  onSelectTurbine: (turbine: Turbine) => void;
};

const TurbineSearch: React.FC<Props> = ({ onSelectTurbine }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTurbines = turbines.filter(turbine =>
	turbine.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
	<div className="turbine-search">
  	<h2 className="title">Введите название турбины</h2>
  	<div className="search-bar">
    	<input
      	type="text"
      	placeholder="A-100"
      	value={searchTerm}
      	onChange={(e) => setSearchTerm(e.target.value)}
      	className="search-input"
    	/>
    	<button className="search-button">Поиск</button>
  	</div>
  	<ul className="turbine-list">
    	{filteredTurbines.map((turbine, index) => (
      	<li key={index} className="turbine-item" onClick={() => onSelectTurbine(turbine)}>
        	<p className="turbine-name">{turbine.name}</p>
        	<p className="turbine-stocks">{turbine.stocks.join(', ')}</p>
      	</li>
    	))}
  	</ul>
	</div>
  );
};

export default TurbineSearch;
