import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Link } from '@tanstack/react-router';

import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import './CalculatorPage.css'; // Этот CSS нужно будет убрать после рефакторинга стилей

export const Route = createFileRoute('/calculator')({
  component: CalculatorPage,
});

function CalculatorPage() {
  const [selectedTurbine, setSelectedTurbine] = useState<any | null>(null);
  const [selectedStock, setSelectedStock] = useState<any | null>(null);
  const [lastCalculation, setLastCalculation] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isResultPage, setIsResultPage] = useState(false);

  const handleTurbineSelect = (turbine: any) => {
    setSelectedTurbine(turbine);
    setSelectedStock(null);
    setIsResultPage(false);
    setLastCalculation(null);
  };

  const handleStockSelect = async (stock: any) => {
      setSelectedStock(stock);
      setIsLoading(true);

      try {
        const stockNameEncoded = encodeURIComponent(stock.name);
        const response = await fetch(`http://10.43.0.105:8000/api/valves/${stockNameEncoded}/results/`);
        if (!response.ok) {
          throw new Error(`Ошибка загрузки результатов: ${response.status}`);
        }

        const results = await response.json();
        if (results.length > 0) {
          const sortedResults = results.sort(
            (a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          );
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
      setIsResultPage(true);
    } else {
      setLastCalculation(null);
    }
  };

  // Обработка отправки данных с StockInputPage
  const handleStockInputSubmit = async (inputData: any) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://10.43.0.105:8000/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inputData),
      });

      if (!response.ok) {
        throw new Error(`Ошибка HTTP: ${response.status}`);
      }

      const result = await response.json();

      setLastCalculation(result);
      setIsResultPage(true);
    } catch (error) {
      console.error('Ошибка при отправке данных:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return <div>Загрузка данных...</div>;
    }

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

    if (lastCalculation) {
      return (
        <EarlyCalculationPage
          stockId={selectedStock.name}
          lastCalculation={lastCalculation}
          onRecalculate={handleRecalculate}
        />
      );
    }

    return <StockInputPage stock={selectedStock} turbine={selectedTurbine} onSubmit={handleStockInputSubmit} />;
  };

  return (
    <div className="calculator-page">
      <header className="header">
        <img src="/logo.png" alt="Logo" className="logo" />
        <h1 className="program-name">WSAPropertiesCalculator</h1>
        <nav className="nav">
          <Link to="/calculator" activeProps={{ style: { fontWeight: 'bold' } }}>Калькулятор</Link>
           <Link to="/about" activeProps={{ style: { fontWeight: 'bold' } }}>О программе</Link>
           <Link to="/help" activeProps={{ style: { fontWeight: 'bold' } }}>Помощь</Link>
        </nav>
      </header>

      <main className="main-content">{renderContent()}</main>

      <footer className="footer">
        <p>© WSAPropsCalculator. АО "Уральский турбинный завод", 2024.</p>
      </footer>
    </div>
  );
};
