import React, { useState, useEffect } from 'react';
import './StockInputPage.css';

type Props = {
  stock: any;
  onSubmit: (data: any) => void;
  initialData?: any; // Добавляем пропс для начальных данных
};

const StockInputPage: React.FC<Props> = ({ stock, onSubmit, initialData }) => {
  const [countParts, setCountParts] = useState(2);

  const [inputData, setInputData] = useState({
    turbine_name: stock.turbine_name || '',
    valve_drawing: stock.valve_drawing || '',
    valve_id: stock.valve_id || '',
    temperature_start: '',
    t_air: '',
    count_valves: countParts,
    p_ejector: Array(countParts).fill(''),
    p_values: Array(3).fill(''),
  });

  useEffect(() => {
    if (initialData) {
      setInputData(initialData);
      setCountParts(initialData.count_valves);
    }
  }, [initialData]);

  const handleInputChange = (e, index = null, arrayName = '') => {
    const { name, value } = e.target;

    if (index !== null && arrayName) {
      setInputData((prevData) => {
        const newValues = [...prevData[arrayName]];
        newValues[index] = value;
        return { ...prevData, [arrayName]: newValues };
      });
    } else {
      setInputData((prevData) => ({ ...prevData, [name]: value }));
    }
  };

  const handleCountPartsChange = (e) => {
    const value = parseInt(e.target.value);
    setCountParts(value);
    setInputData((prevData) => ({
      ...prevData,
      count_valves: value,
      p_ejector: Array(value).fill(''),
    }));
  };

  const handleSubmit = () => {
    console.log('Submitting data:', inputData); // Отладочное сообщение
    onSubmit(inputData);
  };

  return (
    <div className="stock-input-page">
      <h2 className="title">Ввод данных для штока {stock.name}</h2>

      {/* Выбор количества частей */}
      <div className="input-container">
        <label htmlFor="countParts" className="input-label">
          Количество частей (от 2 до 4):
        </label>
        <select
          id="countParts"
          value={countParts}
          onChange={handleCountPartsChange}
          className="stock-input"
        >
          {[2, 3, 4].map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </div>

      {/* Ввод значений для p_ejector */}
      <h3 className="input-label">Введите значения для p_ejector:</h3>
      {inputData.p_ejector.map((value, index) => (
        <input
          key={`p_ejector-${index}`}
          type="number"
          name={`p_ejector-${index}`}
          placeholder={`p_ejector для части ${index + 1}`}
          value={value}
          onChange={(e) => handleInputChange(e, index, 'p_ejector')}
          className="value-input"
        />
      ))}

      {/* Ввод значений для p_values */}
      <h3 className="input-label">Введите значения для p_values (3 элемента):</h3>
      {inputData.p_values.map((value, index) => (
        <input
          key={`p_values-${index}`}
          type="number"
          name={`p_values-${index}`}
          placeholder={`p_value ${index + 1}`}
          value={value}
          onChange={(e) => handleInputChange(e, index, 'p_values')}
          className="value-input"
        />
      ))}

      {/* Остальные параметры */}
      <input
        type="number"
        name="temperature_start"
        placeholder="Начальная температура"
        value={inputData.temperature_start}
        onChange={handleInputChange}
        className="value-input"
      />
      <input
        type="number"
        name="t_air"
        placeholder="Температура воздуха"
        value={inputData.t_air}
        onChange={handleInputChange}
        className="value-input"
      />

      <button className="btn-stock" onClick={handleSubmit}>
        Отправить
      </button>
    </div>
  );
};

export default StockInputPage;
