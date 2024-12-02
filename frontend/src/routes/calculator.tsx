import React, { useState } from 'react';
import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import './CalculatorPage.css';

const CalculatorPage: React.FC = () => {
  const [selectedTurbine, setSelectedTurbine] = useState<any | null>(null); // Выбранная турбина
  const [selectedStock, setSelectedStock] = useState<any | null>(null); // Выбранный шток
  const [lastCalculation, setLastCalculation] = useState<any | null>(null); // Последний расчет для штока
  const [isLoading, setIsLoading] = useState(false); // Состояние загрузки
  const [isResultPage, setIsResultPage] = useState(false); // Переход на страницу результатов

  // Обработка выбора турбины
  const handleTurbineSelect = (turbine) => {
    setSelectedTurbine(turbine);
    setSelectedStock(null);
    setIsResultPage(false);
  };

  // Обработка выбора штока и загрузка предыдущих расчетов
  const handleStockSelect = async (stock) => {
    setSelectedStock(stock);
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/api/valves/${stock.name}/results/`);
      if (!response.ok) {
        throw new Error(`Ошибка загрузки результатов: ${response.status}`);
      }

      const results = await response.json();
      if (results.length > 0) {
        // Берем последний по времени расчет
        const sortedResults = results.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        setLastCalculation(sortedResults[0]);
      } else {
        setLastCalculation(null);
      }
    } catch (error) {
      console.error('Ошибка при загрузке данных:', error);
      setLastCalculation(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Обработка перерасчета или отказа
  const handleRecalculate = (recalculate: boolean) => {
    if (!recalculate) {
      setIsResultPage(true); // Переход на страницу результатов
    } else {
      setLastCalculation(null); // Сброс последнего расчета для ввода новых данных
    }
  };

  // Рендер компонентов в зависимости от состояния
  const renderContent = () => {
    if (isResultPage) {
      return (
        <ResultsPage
          stockId={selectedStock.name}
          inputData={lastCalculation?.input_data}
          outputData={lastCalculation?.output_data}
        />
      );
    }

    if (!selectedTurbine) {
      return <TurbineSearch onSelectTurbine={handleTurbineSelect} />;
    }

    if (!selectedStock) {
      return <StockSelection turbine={selectedTurbine} onSelectValve={handleStockSelect} />;
    }

    if (isLoading) {
      return <div>Загрузка предыдущих расчетов...</div>;
    }

    if (lastCalculation) {
      return <EarlyCalculationPage stockId={selectedStock.name} lastCalculation={lastCalculation} onRecalculate={handleRecalculate} />;
    }

    return <StockInputPage stock={selectedStock} onSubmit={handleRecalculate} />;
  };

  return (
    <div className="calculator-page">
      <header className="header">
        <img src="logo.png" alt="Logo" className="logo" />
        <h1 className="program-name">WSAPropertiesCalculator</h1>
        <nav className="nav">
          <a href="/">Калькулятор</a>
          <a href="/about">О программе</a>
          <a href="/help">Помощь</a>
        </nav>
      </header>

      <main className="main-content">{renderContent()}</main>

      <footer className="footer">
        <p>© WSAPropsCalculator. АО "Уральский турбинный завод", 2024.</p>
      </footer>
    </div>
  );
};

export default CalculatorPage;
