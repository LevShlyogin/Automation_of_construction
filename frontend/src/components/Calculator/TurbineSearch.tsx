import React, { useState, useEffect } from 'react';
import './TurbineSearch.css';

type Turbine = {
  id: number;
  name: string;
};

type Props = {
  onSelectTurbine: (turbine: Turbine) => void;
};

const TurbineSearch: React.FC<Props> = ({ onSelectTurbine }) => {
  const [turbines, setTurbines] = useState<Turbine[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTurbines = async () => {
      try {
        console.log("Отправляем запрос к API...");

        const response = await fetch('http://localhost:8000/turbines/');
        console.log("Статус ответа:", response.status);

        if (!response.ok) {
          throw new Error(`Ошибка загрузки данных. Статус: ${response.status}`);
        }

        const data = await response.json();
        console.log("Полученные данные:", data);
        setTurbines(data);
      } catch (error: any) {
        console.error("Ошибка запроса:", error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTurbines();
  }, []);

  const filteredTurbines = turbines.filter(turbine =>
    turbine.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
            <p className="turbine-name">{turbine.name}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TurbineSearch;
