import React, { useState, useEffect } from 'react';
import './TurbineSearch.css';

type Turbine = {
  id: number;
  turbin_name: string;
  stocks: string[]; // Добавьте это поле, если каждая турбина имеет связанные штоки
};

type Props = {
  onSelectTurbine: (turbine: Turbine) => void;
};

const TurbineSearch: React.FC<Props> = ({ onSelectTurbine }) => {
  const [turbines, setTurbines] = useState<Turbine[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);  // Состояние для индикации загрузки
  const [error, setError] = useState<string | null>(null);  // Состояние для обработки ошибок

  // Загружаем данные о турбинах при монтировании компонента
  useEffect(() => {
    const fetchTurbines = async () => {
      try {
        const response = await fetch('http://localhost:8000/turbines/');
        if (!response.ok) {
          throw new Error('Ошибка загрузки данных');
        }
        const data = await response.json();
        setTurbines(data);  // Сохраняем полученные данные в состояние
      } catch (error: any) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTurbines();
  }, []);

  // Фильтруем турбины по введенному тексту
  const filteredTurbines = turbines.filter(turbine =>
    turbine.turbin_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Обработка загрузки и ошибок
  if (loading) return <div>Загрузка турбин...</div>;
  if (error) return <div>Ошибка: {error}</div>;

  return (
    <div className="turbine-search">
      <h2 className="title">Введите название турбины</h2>
      <div className="search-bar">
        <input
          type="text"
          placeholder="A-100"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>
      <ul className="turbine-list">
        {filteredTurbines.map((turbine) => (
          <li key={turbine.id} className="turbine-item" onClick={() => onSelectTurbine(turbine)}>
            <p className="turbine-name">{turbine.turbin_name}</p>
            {/* Если турбина имеет связанные штоки */}
            {turbine.stocks && (
              <p className="turbine-stocks">Штоки: {turbine.stocks.join(', ')}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TurbineSearch;
