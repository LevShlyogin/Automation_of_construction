import React, { useState } from 'react';
import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import './CalculatorPage.css';

const CalculatorPage: React.FC = () => {
  const [selectedTurbine, setSelectedTurbine] = useState(null);
  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [isRecalculation, setIsRecalculation] = useState(false);

  const handleTurbineSelect = (turbine) => {
	setSelectedTurbine(turbine);
	setSelectedStock(null);
  };

  const handleStockSelect = (stock) => {
	setSelectedStock(stock);
  };

  const handleRecalculate = (recalculate: boolean) => {
	setIsRecalculation(recalculate);
	if (!recalculate) {
  	setSelectedStock(null);
	}
  };

  const handleSubmit = () => {
	// Логика отправки формы
	console.log('Данные отправлены');
  };

  return (
	<div className="calculator-page">
  	<header className="header">
    	<img src="/path/to/logo.png" alt="Logo" className="logo" />
    	<h1 className="program-name">WSAPropertiesCalculator</h1>
    	<nav className="nav">
      	<a href="/">Калькулятор</a>
      	<a href="/about">О программе</a>
      	<a href="/help">Помощь</a>
    	</nav>
  	</header>

  	<main className="main-content">
    	{!selectedTurbine ? (
      	<TurbineSearch onSelectTurbine={handleTurbineSelect} />
    	) : !selectedStock ? (
      	<StockSelection turbine={selectedTurbine} onSelectStock={handleStockSelect} />
    	) : !isRecalculation ? (
      	<EarlyCalculationPage stockId={selectedStock} onRecalculate={handleRecalculate} />
    	) : (
      	<StockInputPage stockId={selectedStock} onSubmit={handleSubmit} />
    	)}
  	</main>

  	<footer className="footer">
    	<p>© WSAPropsCalculator. АО "Уральский турбинный завод", 2024.</p>
  	</footer>
	</div>
  );
};

export default CalculatorPage;
