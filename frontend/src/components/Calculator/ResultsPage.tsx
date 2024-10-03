import React from 'react';
import './ResultsPage.css'

type Props = {
  stockId: string;
};

const ResultsPage: React.FC<Props> = ({ stockId }) => {
  return (
	<div className="results-page">
  	<h2>Шток {stockId}</h2>
  	<p>Все параметры успешно вычислены</p>
  	{/*
  	<table>
    	<thead>
      	<tr>
        	<th>Параметр</th>
        	<th>Значение</th>
      	</tr>
    	</thead>
    	<tbody>
    	</tbody>
  	</table>
  	*/}
  	<div className="buttons">
    	<button className="btn-green-excel">Сохранить в виде Excel</button>
    	<button className="btn-blue-db">Сохранить в базе данных</button>
  	</div>
	</div>
  );
};

export default ResultsPage;
