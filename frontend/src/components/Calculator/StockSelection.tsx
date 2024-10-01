import React from 'react';
import './StockSelection.css'; // Подключаем стили


type Turbine = {
  name: string;
  stocks: string[];
};


type Props = {
  turbine: Turbine | null;
  onSelectStock: (stock: string) => void;
};


const StockSelection: React.FC<Props> = ({ turbine, onSelectStock }) => {
  if (!turbine) return <p>Сначала выберите турбину.</p>;


  return (
	<div className="stock-selection">
  	<h2 className="title">Выберите требуемый шток для {turbine.name}</h2>
  	<ul className="stock-list">
    	{turbine.stocks.map((stock, index) => (
      	<li key={index} className="stock-item" onClick={() => onSelectStock(stock)}>
        	{stock}
      	</li>
    	))}
  	</ul>
	</div>
  );
};


export default StockSelection;
