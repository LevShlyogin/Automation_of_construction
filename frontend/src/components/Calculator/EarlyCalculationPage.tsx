import React from 'react';
import './EarlyCalculationPage.css'; // Подключаем стили

type Props = {
  stockId: string;
  onRecalculate: (recalculate: boolean) => void;
};

const EarlyCalculationPage: React.FC<Props> = ({ stockId, onRecalculate }) => {
  return (
	<div className="detected-calculation">
  	<h2>Шток {stockId}</h2>
  	<h3>Обнаружен предыдущий расчет</h3>
  	<img src="/path/to/calculation-image.png" alt="Previous Calculation" className="calculation-img" />
  	<h3>Хотите провести перерасчет?</h3>
  	<div className="buttons">
    	<button onClick={() => onRecalculate(false)} className="btn red">Нет</button>
    	<button onClick={() => onRecalculate(true)} className="btn green">Да</button>
  	</div>
	</div>
  );
};

export default EarlyCalculationPage;
