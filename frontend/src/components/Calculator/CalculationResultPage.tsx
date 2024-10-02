import React from 'react';
import './CalculationResultsPage.css';

type Props = {
  stockId: string;
  data: Array<Array<string | number>>; // Данные для таблицы (двумерный массив)
  onSaveExcel: () => void;
  onSaveDatabase: () => void;
  saveStatus: string; // Статус сохранения (успешно или ошибка)
};

const CalculationResultsPage: React.FC<Props> = ({ stockId, data, onSaveExcel, onSaveDatabase, saveStatus }) => {
  return (
	<div className="calculation-results-page">
  	<h2>Шток {stockId}</h2>
  	<p>Все параметры успешно высчитаны</p>
  	<table className="results-table">
    	<thead>
      	<tr>
        	<th>Параметр</th>
        	<th>Значение 1</th>
        	<th>Значение 2</th>
        	<th>Значение 3</th>
        	<th>Значение 4</th>
      	</tr>
    	</thead>
    	<tbody>
      	{data.map((row, index) => (
        	<tr key={index}>
          	{row.map((cell, cellIndex) => (
            	<td key={cellIndex}>{cell}</td>
          	))}
        	</tr>
      	))}
    	</tbody>
  	</table>
  	<div className="buttons">
    	<button onClick={onSaveExcel} className="btn green">Сохранить в виде Excel</button>
    	<button onClick={onSaveDatabase} className="btn blue">Сохранить в базе данных</button>
  	</div>
  	{saveStatus && <p className="save-status">{saveStatus}</p>}
	</div>
  );
};

export default CalculationResultsPage;
