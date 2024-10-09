import React from 'react';
import './EarlyCalculationPage.css'; // Подключаем стили

type Props = {
  stockId: string;
  onRecalculate: (recalculate: boolean) => void;
};

const EarlyCalculationPage: React.FC<Props> = ({ stockId, onRecalculate }) => {
  // Example data
  const gi = [1000.0, 900.0, 800.0, 700.0, 600.0];
  const pi_in = [10.0, 9.0, 8.0, 7.0, 6.0];
  const ti = [300.0, 290.0, 280.0, 270.0, 260.0];
  const hi = [2800.0, 2700.0, 2600.0, 2500.0, 2400.0];
  const deaeratorProps = [500.0, 150.0, 0.1, 850.0];
  const ejectorProps = [100.0, 80.0, 0.2, 700.0];

  return (
    <div className="detected-calculation">
      <h2>Шток {stockId}</h2>
      <h3>Обнаружен предыдущий расчет</h3>

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

      <h3>Свойства деаэратор и эжектора</h3>
      <table className="props-table">
        <thead>
          <tr>
            <th>Тип</th>
            <th>Значение</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Деаэратор</td>
            <td>{deaeratorProps.join(', ')}</td>
          </tr>
          <tr>
            <td>Эжектор</td>
            <td>{ejectorProps.join(', ')}</td>
          </tr>
        </tbody>
      </table>

      <h3>Хотите провести перерасчет?</h3>
      <div className="buttons">
        <button onClick={() => onRecalculate(false)} className="btn red">Нет</button>
        <button onClick={() => onRecalculate(true)} className="btn green">Да</button>
      </div>
    </div>
  );
};

export default EarlyCalculationPage;
