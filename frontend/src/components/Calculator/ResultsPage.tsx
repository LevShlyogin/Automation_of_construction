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

  // Функция для округления чисел
  const roundNumber = (num: number, decimals: number = 4) => {
    return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
  };

  // Вывод данных в консоль
  useEffect(() => {
    console.group(`Результаты для клапана: ${stockId}`);
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
    const inputWs = XLSX.utils.json_to_sheet(inputDataFlat, { header: ['Название турбины', 'Чертёж клапана', 'id клапана', 'Начальная температура', 'Температура воздуха', 'Количество участков', 'Выходные давления', 'Входные давления'] });
    XLSX.utils.book_append_sheet(wb, inputWs, 'Входные данные');

    // Преобразование outputData в плоский формат
    const outputDataFlat = flattenData(outputData);
    const outputWs = XLSX.utils.json_to_sheet(outputDataFlat, { header: ['Расход, т/ч', 'Давление , МПа', 'Температура , С', 'Энтальпия , кДж/кг', 'Параметры эжекторов', 'Параметры деаэратора'] });
    XLSX.utils.book_append_sheet(wb, outputWs, 'Выходные данные');

    XLSX.writeFile(wb, `Расчет_${stockId}.xlsx`);
  };

  // Обработчик для отображения сообщения о сохранении в базе данных
  const handleSaveToDatabase = () => {
    setIsSaved(true);
  };

  return (
    <div className="calculation-results-page">
      <h2>Результаты расчётов для клапана: {stockId}</h2>

      <h3>Входные данные</h3>
      {Object.keys(inputData).length > 0 ? (
        <table className="results-table">
          <thead>
            <tr>
              <th>Название турбины</th>
              <th>Чертёж клапана</th>
              <th>id клапана</th>
              <th>Начальная температура</th>
              <th>Температура воздуха</th>
              <th>Количество участков</th>
              <th>Выходные давления</th>
              <th>Входные давления</th>
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
      {outputData.Gi && outputData.Gi.length > 0 ? (
        <table className="results-table">
          <thead>
            <tr>
              <th>Расход, т/ч</th>
              <th>Давление , МПа</th>
              <th>Температура , С</th>
              <th>Энтальпия , кДж/кг</th>
            </tr>
          </thead>
          <tbody>
            {outputData.Gi.map((value: any, index: number) => (
              <tr key={index}>
                <td>{roundNumber(value)}</td>
                <td>{roundNumber(outputData.Pi_in[index])}</td>
                <td>{roundNumber(outputData.Ti[index])}</td>
                <td>{roundNumber(outputData.Hi[index])}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>Нет доступных выходных данных.</p>
      )}

      <h3>Параметры потребителей</h3>
      {outputData.ejector_props && outputData.ejector_props.length > 0 ? (
        <table className="results-table">
          <thead>
            <tr>
              {Object.keys(outputData.ejector_props[0]).map((key, index) => (
                <th key={index}>{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {outputData.ejector_props.map((item: any, index: number) => (
              <tr key={index}>
                {Object.entries(item).map(([_, val]: [string, any], idx) => (
                  <td key={idx}>{roundNumber(val)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>Нет доступных параметров потребителей.</p>
      )}

      <h3>Потребитель 1</h3>
      {outputData.deaerator_props && outputData.deaerator_props.length > 0 ? (
        <table className="results-table">
          <thead>
            <tr>
              {outputData.deaerator_props.map((_: any, index: number) => (
                <th key={index}>{index + 1}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {outputData.deaerator_props.map((value: any, index: number) => (
                <td key={index}>{roundNumber(value)}</td>
              ))}
            </tr>
          </tbody>
        </table>
      ) : (
        <p>Нет доступных данных для потребителя 1.</p>
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
