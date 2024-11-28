import React, { useState } from 'react';
import './StockInputPage.css';

type Props = {
  stock: any;
  onSubmit: (data: any) => void;
};

const StockInputPage: React.FC<Props> = ({ stock, onSubmit }) => {
  const [inputData, setInputData] = useState({
    gi: Array(stock.countParts).fill(''),
    pi_in: '',
    ti: '',
    hi: ''
  });

  const handleInputChange = (e, index = null) => {
    const { name, value } = e.target;

    if (index !== null) {
      setInputData((prevData) => {
        const newValues = [...prevData[name]];
        newValues[index] = value;
        return { ...prevData, [name]: newValues };
      });
    } else {
      setInputData((prevData) => ({ ...prevData, [name]: value }));
    }
  };

  const handleSubmit = () => {
    onSubmit(inputData);
  };

  return (
    <div className="stock-input-page">
      <h2>Ввод данных для штока {stock.name}</h2>

      <h3>Ввод значений Gi для {stock.countParts} частей:</h3>
      {inputData.gi.map((value, index) => (
        <input
          key={index}
          type="number"
          name="gi"
          value={value}
          placeholder={`Gi для части ${index + 1}`}
          onChange={(e) => handleInputChange(e, index)}
        />
      ))}

      <input
        type="number"
        name="pi_in"
        placeholder="Введите Pi_in"
        value={inputData.pi_in}
        onChange={handleInputChange}
      />
      <input
        type="number"
        name="ti"
        placeholder="Введите Ti"
        value={inputData.ti}
        onChange={handleInputChange}
      />
      <input
        type="number"
        name="hi"
        placeholder="Введите Hi"
        value={inputData.hi}
        onChange={handleInputChange}
      />

      <button className="submit-btn" onClick={handleSubmit}>
        Отправить
      </button>
    </div>
  );
};

export default StockInputPage;
