import React, { useState, useEffect } from 'react';
import './StockInputPage.css';

type Props = {
  stock: any;
  turbine: any;
  onSubmit: (data: any) => void;
  initialData?: any;
};

const StockInputPage: React.FC<Props> = ({ stock, turbine, onSubmit, initialData }) => {
  const [countParts, setCountParts] = useState(2);

  const [inputData, setInputData] = useState({
    turbine_name: turbine.name || '',
    valve_drawing: stock.name || '',
    valve_id: stock.id || '',
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
    const parsedValue = value === '' ? '' : parseFloat(value);

    if (index !== null && arrayName) {
      setInputData((prevData) => {
        const newValues = [...prevData[arrayName]];
        newValues[index] = parsedValue;
        return { ...prevData, [arrayName]: newValues };
      });
    } else {
      setInputData((prevData) => ({ ...prevData, [name]: parsedValue }));
    }
  };

  const handleCountPartsChange = (e) => {
    const value = parseInt(e.target.value, 10);
    setCountParts(value);
    setInputData((prevData) => ({
      ...prevData,
      count_valves: value,
      p_ejector: Array(value).fill(''),
    }));
  };

  const handleSubmit = () => {
    console.log('Submitting data:', inputData);
    console.log('Stock values:', {
      name: stock.name,
      id: stock.id,
    });

    onSubmit(inputData);
  };

  return (
    <div className="stock-input-page">
      <h2 className="title">Ввод данных для клапана {stock.name}</h2>

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
      <div className="input-group">
        <h3 className="input-label">Введите значения для p_ejector:</h3>
        {inputData.p_ejector.map((value, index) => (
          <input
            key={`p_ejector-${index}`}
            type="number"
            step="any"
            placeholder={`p_ejector для части ${index + 1}`}
            value={value}
            onChange={(e) => handleInputChange(e, index, 'p_ejector')}
            className="value-input"
          />
        ))}
      </div>

      {/* Ввод значений для p_values */}
      <div className="input-group">
        <h3 className="input-label">Введите значения для p_values (3 элемента):</h3>
        {inputData.p_values.map((value, index) => (
          <input
            key={`p_values-${index}`}
            type="number"
            step="any"
            placeholder={`p_value ${index + 1}`}
            value={value}
            onChange={(e) => handleInputChange(e, index, 'p_values')}
            className="value-input"
          />
        ))}
      </div>

      {/* Ввод температурных значений */}
      <div className="input-group">
        <h3 className="input-label">Введите температурные значения:</h3>
        <input
          type="number"
          step="any"
          name="temperature_start"
          placeholder="Начальная температура"
          value={inputData.temperature_start}
          onChange={handleInputChange}
          className="value-input"
        />
        <input
          type="number"
          step="any"
          name="t_air"
          placeholder="Температура воздуха"
          value={inputData.t_air}
          onChange={handleInputChange}
          className="value-input"
        />
      </div>

      {/* Кнопка отправки */}
      <button className="btn-stock" onClick={handleSubmit}>
        Отправить
      </button>
    </div>
  );
};

export default StockInputPage;