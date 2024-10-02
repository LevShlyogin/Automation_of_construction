import React, { useState } from 'react';
import './StockInputPage.css';

type Props = {
  stockId: string;
  onSubmit: (data: any) => void;
};

const StockInputPage: React.FC<Props> = ({ stockId, onSubmit }) => {
  const [formData, setFormData] = useState({
	p0: '',
	t0: '',
	p1: '',
	p2: ''
  });

  const handleChange = (e) => {
	const { name, value } = e.target;
	setFormData(prevData => ({
  	...prevData,
  	[name]: value
	}));
  };

  const handleSubmit = (e) => {
	e.preventDefault();
	onSubmit(formData); // Передаем данные формы для валидации и отправки
  };

  return (
	<div className="stock-input-page">
  	<h2>Шток {stockId}</h2>
  	<h3>Введите недостающие данные</h3>
  	<form onSubmit={handleSubmit}>
    	<input type="text" name="p0" placeholder="P0" className="value-input" value={formData.p0} onChange={handleChange} />
    	<input type="text" name="t0" placeholder="T0" className="value-input" value={formData.t0} onChange={handleChange} />
    	<input type="text" name="p1" placeholder="P1" className="value-input" value={formData.p1} onChange={handleChange} />
    	<input type="text" name="p2" placeholder="P2" className="value-input" value={formData.p2} onChange={handleChange} />
    	<button type="submit" className="btn-stock">Отправить</button>
  	</form>
	</div>
  );
};

export default StockInputPage;
