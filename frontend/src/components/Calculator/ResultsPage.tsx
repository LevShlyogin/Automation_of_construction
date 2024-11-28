import React, { useEffect } from 'react';
import './ResultsPage.css';

type Props = {
  stockId: string;
  inputData?: Record<string, any>; // Делаем inputData и outputData необязательными
  outputData?: Record<string, any>;
};

const ResultsPage: React.FC<Props> = ({ stockId, inputData = {}, outputData = {} }) => {
  // Вывод данных в консоль
  useEffect(() => {
    console.group(`Результаты для штока: ${stockId}`);

    console.log('Входные данные:');
    if (Object.keys(inputData).length > 0) {
      Object.entries(inputData).forEach(([key, value]) => {
        console.log(`  ${key}:`, JSON.stringify(value));
      });
    } else {
      console.log('  Нет доступных входных данных.');
    }

    console.log('Выходные данные:');
    if (Object.keys(outputData).length > 0) {
      Object.entries(outputData).forEach(([key, value]) => {
        console.log(`  ${key}:`, JSON.stringify(value));
      });
    } else {
      console.log('  Нет доступных выходных данных.');
    }

    console.groupEnd();
  }, [stockId, inputData, outputData]);

  return (
    <div className="results-page">
      <h2>Результаты расчетов для штока: {stockId}</h2>

      <h3>Входные данные</h3>
      {Object.keys(inputData).length > 0 ? (
        <table className="calculation-table">
          <thead>
            <tr>
              {Object.keys(inputData).map((key) => (
                <th key={key}>{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {Object.values(inputData).map((value, index) => (
                <td key={index}>
                  {Array.isArray(value) ? value.join(', ') : value.toString()}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      ) : (
        <p>Нет доступных входных данных.</p>
      )}

      <h3>Выходные данные</h3>
      {Object.keys(outputData).length > 0 ? (
        <table className="calculation-table">
          <thead>
            <tr>
              {Object.keys(outputData).map((key) => (
                <th key={key}>{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {Object.values(outputData).map((value, index) => (
                <td key={index}>
                  {Array.isArray(value) ? value.join(', ') : value.toString()}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      ) : (
        <p>Нет доступных выходных данных.</p>
      )}

      <div className="buttons">
        <button className="btn-green-excel">Сохранить в виде Excel</button>
        <button className="btn-blue-db">Сохранить в базе данных</button>
      </div>
    </div>
  );
};

export default ResultsPage;
