// import React from 'react';
//
// type Turbine = {
//   name: string;
//   stocks: string[];
// };
//
// type Props = {
//   turbine: Turbine | null;
//   onSelectStock: (stock: string) => void;
// };
//
// const StockSelection: React.FC<Props> = ({ turbine, onSelectStock }) => {
//   if (!turbine) return <p>Сначала выберите турбину.</p>;
//
//   return (
// 	<div className="stock-selection">
//   	<h2>Выберите требуемый шток для {turbine.name}</h2>
//   	<ul>
//     	{turbine.stocks.map((stock, index) => (
//       	<li key={index} onClick={() => onSelectStock(stock)}>
//         	{stock}
//       	</li>
//     	))}
//   	</ul>
// 	</div>
//   );
// };
//
// export default StockSelection;


import React from 'react';

const StockSelection = () => {
  return <div><h1>Stock Selection Component</h1></div>;
};

export default StockSelection;
