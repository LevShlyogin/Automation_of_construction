import React, { useState } from 'react';
import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import './CalculatorPage.css';

const CalculatorPage: React.FC = () => {
  const [selectedTurbine, setSelectedTurbine] = useState(null);
  const [selectedStock, setSelectedStock] = useState<any | null>(null);
  const [lastCalculation, setLastCalculation] = useState<any | null>(null); // Для сохранения последнего расчета
  const [isResultPage, setIsResultPage] = useState(false);

  // При выборе турбины
  const handleTurbineSelect = (turbine) => {
    setSelectedTurbine(turbine);
    setSelectedStock(null);
    setIsResultPage(false);
  };

  // При выборе штока
  const handleStockSelect = async (stock) => {
      setSelectedStock(stock);

      // Проверка наличия результатов
      const response = await fetch(`http://localhost:8000/api/valves/${stock.name}/results/`);
      const results = await response.json();

      if (results.length > 0) {
        // Сортируем результаты по времени и берем самый последний
        const sortedResults = results.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        setLastCalculation(sortedResults[0]); // Берем последний по времени расчет
      } else {
        setLastCalculation(null); // Если результатов нет
      }
  };


  // Логика после перерасчета
  const handleRecalculate = (recalculate: boolean) => {
    if (!recalculate) {
      setIsResultPage(true); // Переход на страницу результатов при отказе от перерасчета
    } else {
      setLastCalculation(null); // Обнуление последнего расчета для ввода новых данных
    }
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

      <main className="main-content">
        {isResultPage ? (
          <ResultsPage stockId={selectedStock.name} />
        ) : !selectedTurbine ? (
          <TurbineSearch onSelectTurbine={handleTurbineSelect} />
        ) : !selectedStock ? (
          <StockSelection turbine={selectedTurbine} onSelectValve={handleStockSelect} />
        ) : lastCalculation ? (
          <EarlyCalculationPage
            stockId={selectedStock.name}
            lastCalculation={lastCalculation}
            onRecalculate={handleRecalculate}
          />
        ) : (
          <StockInputPage stock={selectedStock} onSubmit={handleRecalculate} />
        )}
      </main>

      <footer className="footer">
        <p>© WSAPropsCalculator. АО "Уральский турбинный завод", 2024.</p>
      </footer>
    </div>
  );
};

export default CalculatorPage;
