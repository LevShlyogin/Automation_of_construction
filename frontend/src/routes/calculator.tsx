import { useState } from 'react';
// Добавляем импорт createFileRoute
import { createFileRoute } from '@tanstack/react-router';

import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import './CalculatorPage.css'; // Этот CSS нужно будет убрать после рефакторинга стилей

// --- Создаем и экспортируем Route для TanStack Router ---
export const Route = createFileRoute('/calculator')({
  component: CalculatorPage, // Указываем основной компонент этой страницы
  // Здесь можно добавить loader, beforeLoad, validateSearch и т.д., если нужно будет
});

// Основной компонент страницы остается как есть (но помним про рефакторинг fetch, стилей и т.д.)
function CalculatorPage() {
  const [selectedTurbine, setSelectedTurbine] = useState<any | null>(null);
  const [selectedStock, setSelectedStock] = useState<any | null>(null);
  const [lastCalculation, setLastCalculation] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isResultPage, setIsResultPage] = useState(false);

  // Обработка выбора турбины
  const handleTurbineSelect = (turbine: any) => {
    setSelectedTurbine(turbine);
    setSelectedStock(null);
    setIsResultPage(false);
    setLastCalculation(null);
  };

  // Обработка выбора штока и загрузка предыдущих расчетов
  const handleStockSelect = async (stock: any) => {
      setSelectedStock(stock);
      setIsLoading(true);

      try {
        // !!! ВАЖНО: Этот fetch нужно будет переписать на API клиент + TanStack Query !!!
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
       // !!! ВАЖНО: Этот fetch нужно будет переписать на API клиент + TanStack Query !!!
      const response = await fetch('http://10.43.0.105:8000/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inputData),
      });

      if (!response.ok) {
        throw new Error(`Ошибка HTTP: ${response.status}`);
      }

      const result = await response.json();

      // Set the calculation result and navigate to the results page
      setLastCalculation(result);
      setIsResultPage(true);
    } catch (error) {
      console.error('Ошибка при отправке данных:', error);
      // Optionally, display an error message to the user
    } finally {
      setIsLoading(false);
    }
  };

  // Рендер компонентов в зависимости от состояния
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

  // !!! ВАЖНО: Этот header и footer нужно будет удалить, т.к. страница
  // будет рендериться внутри _layout.tsx, у которого уже есть Sidebar !!!
  return (
    <div className="calculator-page">
      <header className="header">
        <img src="/logo.png" alt="Logo" className="logo" />
        <h1 className="program-name">WSAPropertiesCalculator</h1>
        <nav className="nav">
            {/* !!! ВАЖНО: Эти <a> теги нужно заменить на <Link> из TanStack Router !!! */}
          <a href="/calculator">Калькулятор</a>
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
