import React from 'react';

type Props = {
  stockId: string | null;
};

const ResultsPage: React.FC<Props> = ({ stockId }) => {
  return (
	<div className="results-page">
  	<h2>Результаты для штока {stockId}</h2>
  	<p>Здесь можно добавить логику отображения результатов расчетов.</p>
	</div>
  );
};

export default ResultsPage;
