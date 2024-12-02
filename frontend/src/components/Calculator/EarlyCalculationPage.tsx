import React, { useEffect } from 'react';
import './EarlyCalculationPage.css';

type Props = {
  stockId: string;
  lastCalculation: any;
  onRecalculate: (recalculate: boolean, initialData?: any) => void;
};

const EarlyCalculationPage: React.FC<Props> = ({ stockId, lastCalculation, onRecalculate }) => {
  const gi = lastCalculation?.output_data.Gi || [];
  const pi_in = lastCalculation?.output_data.Pi_in || [];
  const ti = lastCalculation?.output_data.Ti || [];
  const hi = lastCalculation?.output_data.Hi || [];
  const deaeratorProps = lastCalculation?.output_data.deaerator_props || [];
  const ejectorProps = lastCalculation?.output_data.ejector_props || [];
  const inputData = lastCalculation?.input_data || {}; // Входные данные

  // Вывод входных и выходных данных в консоль для диагностики
  useEffect(() => {
    console.group(`Данные для штока: ${stockId}`);
    console.log('lastCalculation:', lastCalculation);
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
      <h2>Шток {stockId}</h2>
      <h3>Обнаружен предыдущий расчет</h3>

      {/* Входные данные */}
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
                <td key={index}>{value}</td>
              ))}
            </tr>
          </tbody>
        </table>
      ) : (
        <p>Нет доступных входных данных.</p>
      )}

      {/* Выходные данные */}
      <h3>Выходные данные</h3>
      {gi.length > 0 ? (
        <table className="calculation-table">
          <thead>
            <tr>
              <th>Gi</th>
              <th>Pi_in</th>
              <th>Ti</th>
              <th>Hi</th>
            </tr>
          </thead>
          <tbody>
            {gi.map((value, index) => (
              <tr key={index}>
                <td>{value}</td>
                <td>{pi_in[index]}</td>
                <td>{ti[index]}</td>
                <td>{hi[index]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>Нет доступных выходных данных.</p>
      )}

      <h3 className="question-before-buttons">Желаете провести перерасчет?</h3>
      <div className="buttons">
        <button onClick={() => onRecalculate(false)} className="btn red">
          Нет
        </button>
        <button onClick={() => onRecalculate(true, inputData)} className="btn green">
          Да
        </button>
      </div>
    </div>
  );
};

export default EarlyCalculationPage;
