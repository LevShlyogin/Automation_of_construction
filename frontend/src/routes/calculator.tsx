// import React, { useState } from 'react';
// import TurbineSearch from '../components/Calculator/TurbineSearch';
// import StockSelection from '../components/Calculator/StockSelection';
//
// const CalculatorPage: React.FC = () => {
//   const [selectedTurbine, setSelectedTurbine] = useState(null);
//   const [selectedStock, setSelectedStock] = useState(null);
//
//   const handleTurbineSelect = (turbine) => {
// 	setSelectedTurbine(turbine);
// 	setSelectedStock(null);
//   };
//
//   const handleStockSelect = (stock) => {
// 	setSelectedStock(stock);
//   };
//
//   return (
// 	<div>
//   	{!selectedTurbine ? (
//     	<TurbineSearch onSelectTurbine={handleTurbineSelect} />
//   	) : (
//     	<StockSelection turbine={selectedTurbine} onSelectStock={handleStockSelect} />
//   	)}
// 	</div>
//   );
// };
//
// export default CalculatorPage;

import React from 'react';
import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';

const CalculatorPage = () => {
  return (
	<div>
  	<h1>Калькулятор</h1>
  	<TurbineSearch />
  	<StockSelection />
	</div>
  );
};

export default CalculatorPage;
