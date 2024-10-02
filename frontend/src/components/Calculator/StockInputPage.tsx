import React from 'react';
import './StockInputPage.css'; // Подключаем стили

type Props = {
  stockId: string;
  onSubmit: () => void;
};

const StockInputPage: React.FC<Props> = ({ stockId, onSubmit }) => {
  return (
	<div className="stock-input-page">
  	<h2>Шток {stockId}</h2>
  	<h3>Введите недостающие данные</h3>
  	<form onSubmit={onSubmit}>
    	<input type="text" placeholder="P0" className="value-input" />
    	<input type="text" placeholder="T0" className="value-input" />
    	<input type="text" placeholder="P1" className="value-input" />
    	<input type="text" placeholder="P2" className="value-input" />
    	<button type="submit" className="btn-stock">Отправить</button>
  	</form>
	</div>
  );
};

export default StockInputPage;
