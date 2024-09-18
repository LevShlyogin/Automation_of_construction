import React, { useState } from 'react';

function InputForm() {
  const [turbineDiameter, setTurbineDiameter] = useState('');
  const [pistonStroke, setPistonStroke] = useState('');

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    if (name === 'turbineDiameter') {
      setTurbineDiameter(value);
    } else if (name === 'pistonStroke') {
      setPistonStroke(value);
    }
  };

  return (
    <form>
      <div>
        <label htmlFor="turbineDiameter">Диаметр турбины:</label>
        <input
          type="number"
          id="turbineDiameter"
          name="turbineDiameter"
          value={turbineDiameter}
          onChange={handleInputChange}
        />
      </div>
      <div>
        <label htmlFor="pistonStroke">Ход поршня:</label>
        <input
          type="number"
          id="pistonStroke"
          name="pistonStroke"
          value={pistonStroke}
          onChange={handleInputChange}
        />
      </div>
      {/* Кнопка расчета будет добавлена позже */}
    </form>
  );
}

export default InputForm;