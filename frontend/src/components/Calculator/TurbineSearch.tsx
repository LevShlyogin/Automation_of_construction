// import React, { useState } from 'react';
//
// type Turbine = {
//   name: string;
//   stocks: string[];
// };
//
// const turbines: Turbine[] = [
//   { name: 'Турбина N-123', stocks: ['NT-123456', 'NT-123456', 'NT-123456'] },
//   { name: 'Турбина N-100', stocks: ['NT-123456', 'NT-654321'] },
//   { name: 'Турбина N-200', stocks: ['NT-333444'] },
// ];
//
// type Props = {
//   onSelectTurbine: (turbine: Turbine) => void;
// };
//
// const TurbineSearch: React.FC<Props> = ({ onSelectTurbine }) => {
//   const [searchTerm, setSearchTerm] = useState('');
//
//   const filteredTurbines = turbines.filter(turbine =>
// 	turbine.name.toLowerCase().includes(searchTerm.toLowerCase())
//   );
//
//   return (
// 	<div className="turbine-search">
//   	<h2>Введите название турбины</h2>
//   	<input
//     	type="text"
//     	placeholder="A-100"
//     	value={searchTerm}
//     	onChange={(e) => setSearchTerm(e.target.value)}
//   	/>
//   	<ul>
//     	{filteredTurbines.map((turbine, index) => (
//       	<li key={index} onClick={() => onSelectTurbine(turbine)}>
//         	{turbine.name}
//         	<br />
//         	{turbine.stocks.join(', ')}
//       	</li>
//     	))}
//   	</ul>
// 	</div>
//   );
// };
//
// export default TurbineSearch;


import React from 'react';

const TurbineSearch = () => {
  return <div><h1>Turbine Search Component</h1></div>;
};

export default TurbineSearch;
