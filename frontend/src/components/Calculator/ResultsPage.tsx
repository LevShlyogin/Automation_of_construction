import React, { useEffect, useState } from 'react';
import * as XLSX from 'xlsx';
import './ResultsPage.css';

type Props = {
  stockId: string;
  inputData?: Record<string, any>; // Делаем inputData и outputData необязательными
  outputData?: Record<string, any>;
};

const ResultsPage: React.FC<Props> = ({ stockId, inputData = {}, outputData = {} }) => {
  const [isSaved, setIsSaved] = useState(false);

  // Вывод данных в консоль
  useEffect(() => {
    console.group(`Результаты для штока: ${stockId}`);
    console.log('inputData:', inputData);
    console.log('outputData:', outputData);
    console.groupEnd();
  }, [stockId, inputData, outputData]);

  // Функция для преобразования данных в плоский формат
  const flattenData = (data: Record<string, any>) => {
    const result: any[] = [];
    const keys = Object.keys(data);
    const maxLength = Math.max(...keys.map(key => Array.isArray(data[key]) ? data[key].length : 1));

    for (let i = 0; i < maxLength; i++) {
      const row: any = {};
      keys.forEach(key => {
        const value = data[key];
        if (Array.isArray(value)) {
          row[key] = value[i] !== undefined ? value[i] : '';
        } else if (i === 0) {
          row[key] = value;
        }
      });
      result.push(row);
    }
    return result;
  };

  // Обработчик для скачивания Excel файла
  const handleDownloadExcel = () => {
    const wb = XLSX.utils.book_new();

    // Преобразование inputData в плоский формат
    const inputDataFlat = flattenData(inputData);
    const inputWs = XLSX.utils.json_to_sheet(inputDataFlat, { header: Object.keys(inputData) });
    XLSX.utils.book_append_sheet(wb, inputWs, 'Input Data');

    // Преобразование outputData в плоский формат
    const outputDataFlat = flattenData(outputData);
    const outputWs = XLSX.utils.json_to_sheet(outputDataFlat, { header: Object.keys(outputData) });
    XLSX.utils.book_append_sheet(wb, outputWs, 'Output Data');

    XLSX.writeFile(wb, `Results_${stockId}.xlsx`);
  };

  // Обработчик для отображения сообщения о сохранении в базе данных
  const handleSaveToDatabase = () => {
    setIsSaved(true);
  };

  return (
    <div className="calculation-results-page">
      <h2>Результаты расчетов для штока: {stockId}</h2>

      <h3>Входные данные</h3>
      {Object.keys(inputData).length > 0 ? (
        <table className="results-table">
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
        <table className="results-table">
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
        <button className="btn-green-excel" onClick={handleDownloadExcel}>
          Сохранить в виде Excel
        </button>
        <button
          className={`btn-blue-db ${isSaved ? 'disabled' : ''}`}
          onClick={handleSaveToDatabase}
          disabled={isSaved}
        >
          Сохранить в базе данных
        </button>
      </div>

      {isSaved && <p className="save-status">Запись успешно сохранена в базе данных!</p>}
    </div>
  );
};

export default ResultsPage;
