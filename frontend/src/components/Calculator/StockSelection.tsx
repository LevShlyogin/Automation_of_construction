import React from 'react';
import './StockSelection.css';

type Valve = {
  id: number;
  name: string;
  type: string | null;
  diameter: number | null;
  clearance: number | null;
  countParts: number | null;
  lenPart1: number | null;
  lenPart2: number | null;
  lenPart3: number | null;
  lenPart4: number | null;
  lenPart5: number | null;
  roundRadius: number;
  sectionLengths: (number | null)[];
};

type Props = {
  turbine: any;
  onSelectValve: (valve: Valve) => void;
};

const StockSelection: React.FC<Props> = ({ turbine, onSelectValve }) => {
  const [valves, setValves] = React.useState<Valve[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchValves = async () => {
      try {
        // Кодируем имя турбины перед использованием в URL
        const turbineNameEncoded = encodeURIComponent(turbine.name);
        const response = await fetch(`http://localhost:8000/api/turbines/${turbineNameEncoded}/valves`);
        if (!response.ok) {
          throw new Error(`Ошибка загрузки данных. Статус: ${response.status}`);
        }
        const data = await response.json();
        setValves(data.valves);
      } catch (error: any) {
        console.error('Ошибка запроса:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };
    fetchValves();
  }, [turbine]);

  if (loading) return <div>Загрузка клапанов...</div>;
  if (error) return <div>Ошибка: {error}</div>;

  return (
    <div className="stock-selection">
      <h2 className="title">Выбранная турбина: {turbine.name}</h2>
      <h3 className="title">Выберите клапан для расчёта</h3>
      <ul className="stock-list">
        {valves.map((valve) => (
          <li key={valve.id} className="stock-item" onClick={() => onSelectValve(valve)}>
            <p className="stock-name">{valve.name}</p>
            <p className="stock-type">{valve.type}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default StockSelection;
