import React, { useEffect } from 'react';
import './EarlyCalculationPage.css';

type Props = {
  stockId: string;
  lastCalculation: any;
  onRecalculate: (recalculate: boolean) => void;
};

const EarlyCalculationPage: React.FC<Props> = ({ stockId, lastCalculation, onRecalculate }) => {
  const gi = lastCalculation?.output_data.Gi || [];
  const pi_in = lastCalculation?.output_data.Pi_in || [];
  const ti = lastCalculation?.output_data.Ti || [];
  const hi = lastCalculation?.output_data.Hi || [];
  const deaeratorProps = lastCalculation?.output_data.deaerator_props || [];
  const ejectorProps = lastCalculation?.output_data.ejector_props || [];
  const inputData = lastCalculation?.input_data || {}; // Входные данные

  // Функция для округления чисел
  const roundNumber = (num: number, decimals: number = 4) => {
    return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
  };

  // Вывод входных и выходных данных в консоль для диагностики
  useEffect(() => {
    console.group(`Данные для клапана: ${stockId}`);
    console.log('Последний расчёт:', lastCalculation);
    console.log('Входные данные:', inputData);
    console.log('Выходные данные:', {
      Gi: gi,
      Pi_in: pi_in,
      Ti: ti,
      Hi: hi,
      deaeratorProps: deaeratorProps,
      ejectorProps: ejectorProps
    });
    console.groupEnd();
  }, [stockId, lastCalculation, inputData, gi, pi_in, ti, hi, deaeratorProps, ejectorProps]);

  return (
    <div className="detected-calculation">
      <h2>Клапан {stockId}</h2>
      <h3>Обнаружен предыдущий расчет</h3>

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
      {gi.length > 0 ? (
        <table className="calculation-table">
          <thead>
            <tr>
              <th>Расход, т/ч</th>
              <th>Давление , МПа</th>
              <th>Температура , С</th>
              <th>Энтальпия , кДж/кг</th>
            </tr>
          </thead>
          <tbody>
            {gi.map((value, index) => (
              <tr key={index}>
                <td>{roundNumber(value)}</td>
                <td>{roundNumber(pi_in[index])}</td>
                <td>{roundNumber(ti[index])}</td>
                <td>{roundNumber(hi[index])}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>Нет доступных выходных данных.</p>
      )}

      {/* Отображение ejector_props */}
      <h3>Параметры потребителей</h3>
      {ejectorProps.length > 0 ? (
        <table className="calculation-table">
          <thead>
            <tr>
              <th>g</th>
              <th>h</th>
              <th>p</th>
              <th>t</th>
            </tr>
          </thead>
          <tbody>
            {ejectorProps.map((prop, index) => (
              <tr key={index}>
                <td>{roundNumber(prop.g)}</td>
                <td>{roundNumber(prop.h)}</td>
                <td>{roundNumber(prop.p)}</td>
                <td>{roundNumber(prop.t)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>Нет доступных данных для параметров потребителей.</p>
      )}

      {/* Отображение deaerator_props */}
      <h3>Потребитель 1</h3>
      {deaeratorProps.length > 0 ? (
        <table className="calculation-table">
          <tbody>
            <tr>
              {deaeratorProps.map((value, index) => (
                <td key={index}>{roundNumber(value)}</td>
              ))}
            </tr>
          </tbody>
        </table>
      ) : (
        <p>Нет доступных данных для потребителя 1.</p>
      )}

      <h3 className="question-before-buttons">Желаете провести перерасчет?</h3>
      <div className="buttons">
        <button onClick={() => onRecalculate(false)} className="btn red">
          Нет
        </button>
        <button onClick={() => onRecalculate(true)} className="btn green">
          Да
        </button>
      </div>
    </div>
  );
};

export default EarlyCalculationPage;