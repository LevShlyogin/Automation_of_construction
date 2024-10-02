import React, { useState } from 'react';
import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import './CalculatorPage.css';

const CalculatorPage: React.FC = () => {
  const [selectedTurbine, setSelectedTurbine] = useState(null);
  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [isRecalculation, setIsRecalculation] = useState(false);
  const [isResultPage, setIsResultPage] = useState(false); // Добавляем состояние для перехода на страницу результатов

  const handleTurbineSelect = (turbine) => {
	setSelectedTurbine(turbine);
	setSelectedStock(null);
	setIsResultPage(false); // Сброс страницы результатов при новом поиске
  };

  const handleStockSelect = (stock) => {
	setSelectedStock(stock);
  };

  const handleRecalculate = (recalculate: boolean) => {
	setIsRecalculation(recalculate);
	if (!recalculate) {
  	setIsResultPage(true); // Переход на страницу результатов при нажатии "Нет"
	} else {
  	setSelectedStock(null); // Очищаем шток для повторного ввода
	}
  };

  const handleSubmit = (data) => {
	// Проверяем и отправляем данные
	if (validateInputs(data)) {
  	console.log('Данные отправлены');
  	setIsResultPage(true); // Переход на страницу результатов
	} else {
  	alert('Пожалуйста, заполните все поля корректно.');
	}
  };

  const validateInputs = (data) => {
	// Проверяем, что все поля содержат числа
	return Object.values(data).every(value => !isNaN(parseFloat(value)));
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
    	{isResultPage ? (
      	<ResultsPage stockId={selectedStock} />
    	) : !selectedTurbine ? (
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
